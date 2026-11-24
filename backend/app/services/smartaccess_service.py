"""SmartAccess 平台集成服务。"""

import logging
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fastapi import HTTPException

from app.core.config import get_settings
from app.core.datetime_utils import format_datetime
from app.repositories.data_asset_repository import DataAssetRepository
from app.repositories.smartaccess_repository import (
    SmartAccessRepository,
    SmartAccessRunNotFoundError,
)
from app.schemas.smartaccess import (
    SmartAccessRunCreateRequest,
    SmartAccessRunEventRequest,
    SmartAccessTemplatePublishRequest,
)
from app.services.smartaccess_workflow_resolver import resolve_runtime_placeholders

logger = logging.getLogger(__name__)

# 任务结束后数据文件仍可能延迟入库的宽限时间(秒)
DATA_BINDING_GRACE_SECONDS = 600
# 运行详情附带的数据结果数量上限
DATA_RESULT_LIMIT = 50


def _build_steps_from_workflow(
    workflow_snapshot: dict,
    events: list[dict],
) -> list[dict]:
    """根据工作流快照和事件构造步骤详情。

    Args:
        workflow_snapshot: 工作流快照。
        events: 事件记录列表。

    Returns:
        步骤详情列表。
    """
    workflow_steps = workflow_snapshot.get("steps", [])
    event_map: dict[str, dict] = {}
    for item in events:
        step_key = item.get("step_id")
        if not step_key and item.get("step_index") is not None:
            step_key = str(item.get("step_index"))
        if step_key:
            event_map[step_key] = item

    items = []
    for index, step in enumerate(workflow_steps):
        step_key = str(step.get("id") or step.get("step_id") or index)
        event = event_map.get(step_key) or event_map.get(str(index))
        if event:
            step_status = event.get("status", "running")
        else:
            step_status = (
                "success"
                if index < int(workflow_snapshot.get("current_step_index", 0))
                else "queued"
            )
        items.append(
            {
                "name": step.get("name")
                or step.get("display_name")
                or step.get("id")
                or step.get("step_id")
                or f"step-{index + 1}",
                "status": step_status,
                "started_at": event.get("created_at", "") if event else "",
                "finished_at": "",
                "description": step.get("action", ""),
                "params": step,
                "result": event.get("payload") if event else None,
            }
        )
    return items


def _project_data_file(item: dict) -> dict:
    """把数据文件记录投影为运行详情展示对象。

    Args:
        item: 数据资产文件记录。

    Returns:
        展示字段字典。
    """
    return {
        "file_id": item.get("file_id", ""),
        "asset_id": item.get("asset_id", ""),
        "filename": item.get("filename", ""),
        "relative_path": item.get("relative_path", ""),
        "asset_group_id": item.get("asset_group_id", ""),
        "device_id": item.get("device_id", ""),
        "data_type": item.get("data_type", ""),
        "file_size": int(item.get("file_size") or 0),
        "storage_uri": item.get("storage_uri", ""),
        "ingested_at": format_datetime(item.get("ingested_at")),
        "bound": bool(item.get("device_run_id")),
    }


def _binding_window(run_record: dict) -> tuple[str, str]:
    """计算运行的数据关联时间窗。

    窗口从任务开始（或请求）时间起，到任务结束时间加宽限期止；
    未结束的任务以当前时间为界。

    Args:
        run_record: SmartAccess 运行记录。

    Returns:
        (开始 ISO 文本, 结束 ISO 文本)；时间不可解析时返回空串使查询跳过。
    """
    start_raw = run_record.get("started_at") or run_record.get("requested_at")
    end_raw = run_record.get("finished_at")
    try:
        start = datetime.fromisoformat(str(start_raw))
        end = (
            datetime.fromisoformat(str(end_raw))
            if end_raw
            else datetime.now(timezone.utc)
        )
    except (TypeError, ValueError):
        return "", ""
    window_end = end + timedelta(seconds=DATA_BINDING_GRACE_SECONDS)
    return start.isoformat(), window_end.isoformat()


class SmartAccessService:
    """SmartAccess 模板和远程运行业务服务。"""

    def __init__(
        self,
        repository: SmartAccessRepository,
        publisher,
        data_repository: DataAssetRepository | None = None,
    ) -> None:
        """初始化服务。

        Args:
            repository: SmartAccess 仓储。
            publisher: SmartAccess MQ 发布器。
            data_repository: SmartDataHub 数据资产仓储，用于任务数据结果关联。
        """
        self._repository = repository
        self._publisher = publisher
        self._data_repository = data_repository

    def publish_template(self, payload: SmartAccessTemplatePublishRequest) -> dict:
        """发布 SmartAccess 模板。

        Args:
            payload: 模板发布请求。

        Returns:
            模板记录。
        """
        if not payload.workflow:
            raise HTTPException(status_code=400, detail="workflow 不能为空")
        return self._repository.publish_template(payload)

    def list_templates(
        self,
        keyword: str | None = None,
        device_id: str | None = None,
        source_device_id: str | None = None,
        status: str | None = None,
    ) -> list[dict]:
        """查询模板列表。

        Args:
            keyword: 搜索关键字。
            device_id: 兼容旧参数，按锚点配置 ID 过滤。
            source_device_id: 发布模板的 SmartAccess 执行端 ID。
            status: 模板状态。

        Returns:
            模板列表。
        """
        records = self._repository.list_templates(
            keyword,
            device_id,
            source_device_id,
            status,
        )
        for item in records:
            item["published_at"] = format_datetime(item.get("published_at"))
        return records

    def get_template(
        self,
        template_id: str,
        template_version: str,
        source_device_id: str | None = None,
    ) -> dict:
        """读取模板详情。

        Args:
            template_id: 模板 ID。
            template_version: 模板版本。
            source_device_id: 发布模板的执行端 ID；提供时优先匹配该执行端的记录。

        Returns:
            模板记录。
        """
        template = self._repository.get_template(
            template_id,
            template_version,
            source_device_id,
        )
        if template is None:
            raise HTTPException(status_code=404, detail="SmartAccess 模板不存在")
        template["published_at"] = format_datetime(template.get("published_at"))
        return template

    def delete_template(
        self,
        template_id: str,
        template_version: str,
        source_device_id: str | None = None,
    ) -> None:
        """删除 SmartAccess 模板。

        Args:
            template_id: 模板 ID。
            template_version: 模板版本。
            source_device_id: 发布模板的执行端 ID；提供时仅删除该执行端的记录。
        """
        if not self._repository.delete_template(
            template_id,
            template_version,
            source_device_id,
        ):
            raise HTTPException(status_code=404, detail="SmartAccess 模板不存在")

    def unpublish_device(self, device_id: str) -> int:
        """下线挂在指定仪器上的已发布模板。

        Args:
            device_id: 仪器设备 ID。

        Returns:
            下线的模板数量。
        """
        return self._repository.delete_templates_by_device(device_id)

    def create_run(self, payload: SmartAccessRunCreateRequest) -> dict:
        """创建 SmartAccess 远程运行并发布 MQ 消息。

        Args:
            payload: 运行创建请求。

        Returns:
            运行记录。
        """
        # 模板按执行端(source_device_id)隔离,优先用执行端 ID 精确匹配;
        # 兼容旧调用方只传 target_device_id 的场景。
        source_device_id = payload.smartaccess_node_id or payload.target_device_id
        template = self.get_template(
            payload.template_id,
            payload.template_version,
            source_device_id,
        )
        try:
            template["workflow"] = resolve_runtime_placeholders(
                template.get("workflow") or {},
                payload.runtime_inputs,
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        run = self._repository.create_run(template, payload)
        self._publisher.publish_run_requested(
            {
                "message_id": f"msg_{run['run_id']}",
                "type": "run.requested",
                "run_id": run["run_id"],
                "template_id": run["template_id"],
                "template_version": run["template_version"],
                "device_id": run["smartaccess_node_id"],
                "smartaccess_node_id": run["smartaccess_node_id"],
                "target_device_id": run["target_device_id"],
                "workflow": run["workflow_snapshot"],
                "requested_by": run["requested_by"],
                "requested_at": run["requested_at"],
            }
        )
        return run

    def list_runs(self) -> list[dict]:
        """查询 SmartAccess 运行列表。

        Returns:
            兼容 SmartAccessRunItem 的运行列表。
        """
        records = self._repository.list_runs()
        return [
            {
                "run_id": item["run_id"],
                "workflow_name": item.get("workflow_name", ""),
                "device_key": item.get("target_device_id", ""),
                "smartaccess_node_id": item.get("smartaccess_node_id", ""),
                "target_device_id": item.get("target_device_id", ""),
                "status": item.get("status", "queued"),
                "current_step_index": int(item.get("current_step_index") or 0),
                "total_steps": int(item.get("total_steps") or 0),
                "started_at": format_datetime(
                    item.get("started_at") or item.get("requested_at")
                ),
                "source": "smartaccess",
            }
            for item in records
        ]

    def get_run(self, run_id: str) -> dict:
        """读取 SmartAccess 运行详情。

        Args:
            run_id: 平台运行 ID。

        Returns:
            运行详情响应字典。
        """
        record = self._repository.get_run(run_id)
        if record is None:
            raise HTTPException(status_code=404, detail="SmartAccess 运行不存在")
        events = [
            {
                "event_id": item.get("event_id", ""),
                "run_id": item.get("run_id", ""),
                "event_type": item.get("event_type", ""),
                "step_id": item.get("step_id", ""),
                "step_index": item.get("step_index"),
                "status": item.get("status", ""),
                "payload": item.get("payload", {}),
                "created_at": item.get("created_at", ""),
            }
            for item in record.get("events", [])
        ]
        workflow_snapshot = dict(record.get("workflow_snapshot") or {})
        workflow_snapshot["current_step_index"] = int(
            record.get("current_step_index") or 0
        )
        detail = {
            "run_id": record["run_id"],
            "workflow_name": record.get("workflow_name", ""),
            "status": record.get("status", "queued"),
            "current_step_index": int(record.get("current_step_index") or 0),
            "total_steps": int(record.get("total_steps") or 0),
            "started_at": format_datetime(
                record.get("started_at") or record.get("requested_at")
            ),
            "finished_at": format_datetime(record.get("finished_at"))
            if record.get("finished_at")
            else "",
            "trigger_source": "smartaccess",
            "operator_name": record.get("requested_by", "system"),
            "source": "smartaccess",
            "template_id": record.get("template_id", ""),
            "template_version": record.get("template_version", ""),
            "smartaccess_node_id": record.get("smartaccess_node_id", ""),
            "target_device_id": record.get("target_device_id", ""),
            "anchor_profile": record.get("anchor_profile", ""),
            "events": events,
            "steps": _build_steps_from_workflow(workflow_snapshot, events),
        }
        data_files, data_suggestions = self._resolve_data_results(record)
        detail["data_files"] = data_files
        detail["data_suggestions"] = data_suggestions
        return detail

    def bind_data_file(self, run_id: str, file_id: str) -> dict:
        """人工确认把数据文件绑定到任务运行。

        Args:
            run_id: 平台运行 ID。
            file_id: 数据文件 ID。

        Returns:
            绑定后的文件投影。

        Raises:
            HTTPException: 运行或文件不存在时抛出。
        """
        if self._repository.get_run(run_id) is None:
            raise HTTPException(status_code=404, detail="SmartAccess 运行不存在")
        if self._data_repository is None:
            raise HTTPException(status_code=503, detail="数据资产服务不可用")
        record = self._data_repository.bind_file_to_run(file_id, run_id)
        if record is None:
            raise HTTPException(status_code=404, detail="数据文件不存在")
        return _project_data_file(record)

    def unbind_data_file(self, run_id: str, file_id: str) -> dict:
        """解除数据文件与任务运行的绑定。

        Args:
            run_id: 平台运行 ID。
            file_id: 数据文件 ID。

        Returns:
            解绑后的文件投影。

        Raises:
            HTTPException: 运行或文件不存在、文件未绑定该运行时抛出。
        """
        if self._repository.get_run(run_id) is None:
            raise HTTPException(status_code=404, detail="SmartAccess 运行不存在")
        if self._data_repository is None:
            raise HTTPException(status_code=503, detail="数据资产服务不可用")
        record = self._data_repository.unbind_file_from_run(file_id, run_id)
        if record is None:
            raise HTTPException(
                status_code=404,
                detail="数据文件不存在或未绑定到该运行",
            )
        return _project_data_file(record)

    def _resolve_data_results(
        self,
        run_record: dict,
    ) -> tuple[list[dict], list[dict]]:
        """解析运行关联的数据文件与时间窗建议关联。

        Args:
            run_record: SmartAccess 运行记录。

        Returns:
            (已绑定文件列表, 建议关联文件列表) 二元组。
        """
        if self._data_repository is None:
            return [], []
        data_files = [
            _project_data_file(item)
            for item in self._data_repository.find_files_by_run(
                run_record["run_id"],
                limit=DATA_RESULT_LIMIT,
            )
        ]
        suggestions = [
            _project_data_file(item)
            for item in self._data_repository.find_unbound_files_in_window(
                [
                    run_record.get("target_device_id"),
                    run_record.get("anchor_profile"),
                    run_record.get("smartaccess_node_id"),
                ],
                *_binding_window(run_record),
                limit=DATA_RESULT_LIMIT,
            )
        ]
        return data_files, suggestions

    def append_event(
        self,
        run_id: str,
        payload: SmartAccessRunEventRequest,
    ) -> dict:
        """追加 SmartAccess 运行事件。

        Args:
            run_id: 平台运行 ID。
            payload: 事件请求。

        Returns:
            事件记录。
        """
        try:
            return self._repository.append_event(run_id, payload)
        except SmartAccessRunNotFoundError as exc:
            raise HTTPException(
                status_code=404,
                detail="SmartAccess 运行不存在",
            ) from exc

    def sweep_stale_runs(self) -> dict[str, int]:
        """扫描并标记超时的 SmartAccess 运行为失败。

        通过追加 run.failed 事件触发既有状态机，前端无需改动即可看到失败结果。

        Returns:
            {"queued": N, "running": M} 两类超时清理数量。
        """
        settings = get_settings().smartaccess
        now = datetime.now(timezone.utc)
        queued_cutoff_iso = (
            now - timedelta(seconds=settings.queued_timeout_seconds)
        ).isoformat()
        step_cutoff_iso = (
            now - timedelta(seconds=settings.step_timeout_seconds)
        ).isoformat()

        stale = self._repository.find_stale_runs(
            queued_cutoff_iso,
            step_cutoff_iso,
        )
        counters = {"queued": 0, "running": 0}

        queued_minutes = settings.queued_timeout_seconds // 60
        step_minutes = settings.step_timeout_seconds // 60

        for run in stale["queued"]:
            self._append_timeout_event(
                run_id=run["run_id"],
                reason="queued_timeout",
                error=f"任务排队超过 {queued_minutes} 分钟未被执行端消费",
            )
            counters["queued"] += 1

        for run in stale["running"]:
            self._append_timeout_event(
                run_id=run["run_id"],
                reason="step_timeout",
                error=f"任务执行超过 {step_minutes} 分钟无进展更新",
            )
            counters["running"] += 1

        if any(counters.values()):
            logger.info(
                "SmartAccess 超时清理：排队超时 %d 个，执行卡死 %d 个",
                counters["queued"],
                counters["running"],
            )
        return counters

    def _append_timeout_event(
        self,
        run_id: str,
        reason: str,
        error: str,
    ) -> None:
        """为超时运行追加 run.failed 事件。

        Args:
            run_id: 平台运行 ID。
            reason: 超时原因标识（queued_timeout / step_timeout）。
            error: 错误描述文本。
        """
        payload = SmartAccessRunEventRequest(
            event_id=f"timeout_{uuid4().hex[:12]}",
            event_type="run.failed",
            status="failed",
            payload={"error": error, "reason": reason},
        )
        try:
            self._repository.append_event(run_id, payload)
        except SmartAccessRunNotFoundError:
            logger.warning("超时清理时运行 %s 不存在，已跳过", run_id)
