"""外部实验任务下发业务服务。"""

from datetime import datetime, timezone
from uuid import uuid4

from fastapi import HTTPException

from app.repositories.external_experiment_dispatch_repository import (
    ExternalExperimentDispatchRepository,
)
from app.schemas.external_experiment_dispatch import (
    ExternalExperimentDispatchCreateRequest,
)


class ExternalExperimentDispatchService:
    """创建和查询外部实验任务批次。"""

    def __init__(self, repository: ExternalExperimentDispatchRepository) -> None:
        """初始化外部实验任务服务。

        Args:
            repository: 外部实验任务仓储。
        """
        self._repository = repository

    @staticmethod
    def _now_text() -> str:
        """返回当前 UTC ISO 时间文本。"""
        return datetime.now(timezone.utc).isoformat()

    def create_dispatch(
        self,
        payload: ExternalExperimentDispatchCreateRequest,
    ) -> dict:
        """创建已接收状态的外部实验任务批次。

        Args:
            payload: 外部系统提交的实验任务信息。

        Returns:
            已保存的实验任务记录。
        """
        now_text = self._now_text()
        record = {
            "dispatch_id": f"ext_exp_{uuid4().hex[:12]}",
            "status": "received",
            "source_system": payload.source_system.strip().lower(),
            "source_module": payload.source_module.strip().lower(),
            "source_reference": payload.source_reference,
            "experiment_name": payload.experiment_name.strip(),
            "experiment_object": payload.experiment_object.model_dump(),
            "experiment_content": payload.experiment_content,
            "conditions": [item.model_dump() for item in payload.conditions],
            "optimization_context": payload.optimization_context,
            "extra_metadata": payload.extra_metadata,
            "received_at": now_text,
        }
        return self._repository.create(record)

    def list_dispatches(self, keyword: str | None = None) -> list[dict]:
        """查询外部实验任务列表。

        Args:
            keyword: 按任务、对象或来源筛选的关键词。

        Returns:
            用于列表展示的任务记录。
        """
        records = self._repository.list(keyword.strip() if keyword else None)
        return [
            {
                "dispatch_id": item["dispatch_id"],
                "status": item.get("status", "received"),
                "source_system": item.get("source_system", ""),
                "source_module": item.get("source_module", ""),
                "experiment_name": item.get("experiment_name", ""),
                "experiment_object": item.get("experiment_object", {}),
                "condition_count": len(item.get("conditions", [])),
                "source_reference": item.get("source_reference", {}),
                "received_at": item.get("received_at", ""),
            }
            for item in records
        ]

    def get_dispatch(self, dispatch_id: str) -> dict:
        """查询外部实验任务详情。

        Args:
            dispatch_id: 外部实验任务批次标识。

        Returns:
            外部实验任务完整记录。

        Raises:
            HTTPException: 任务批次不存在时抛出 404。
        """
        record = self._repository.get(dispatch_id)
        if record is None:
            raise HTTPException(status_code=404, detail="外部实验任务不存在")
        record["condition_count"] = len(record.get("conditions", []))
        return record
