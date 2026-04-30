"""工作流仓储实现。"""

from datetime import datetime, timezone
from uuid import uuid4

from app.domain.enums import StepRunStatus, WorkflowRunStatus
from app.domain.models import (
    WorkflowDefinitionCreate,
    WorkflowDefinitionRecord,
    WorkflowRunRecord,
)


class WorkflowRepository:
    """工作流定义与运行记录仓储。"""

    def __init__(self, database) -> None:
        """初始化工作流仓储。

        Args:
            database: MongoDB 数据库实例。
        """
        self._definitions = database["workflow_definitions"]
        self._runs = database["workflow_runs"]

    def create_definition(
        self,
        definition: WorkflowDefinitionCreate,
    ) -> WorkflowDefinitionRecord:
        """创建工作流定义。

        Args:
            definition: 待创建的工作流定义。

        Returns:
            持久化后的工作流定义记录。
        """
        record = WorkflowDefinitionRecord(
            workflow_id=str(uuid4()),
            created_at=datetime.now(timezone.utc),
            **definition.model_dump(),
        )
        self._definitions.insert_one(record.model_dump(mode="python"))
        return record

    def create_run(self, definition: WorkflowDefinitionRecord) -> WorkflowRunRecord:
        """根据工作流定义创建运行记录。

        Args:
            definition: 已持久化的工作流定义。

        Returns:
            新建的工作流运行记录。
        """
        run = WorkflowRunRecord.from_definition(definition)
        self._runs.insert_one(run.model_dump(mode="python"))
        return run

    def list_definitions(self) -> list[dict]:
        """列出所有工作流定义记录。

        Returns:
            按创建时间倒序排列的工作流定义列表。
        """
        return list(self._definitions.find().sort("created_at", -1))

    def get_run(self, run_id: str) -> dict | None:
        """根据运行标识获取工作流运行记录。

        Args:
            run_id: 工作流运行标识。

        Returns:
            对应运行记录，若不存在则返回 None。
        """
        return self._runs.find_one({"run_id": run_id})

    def list_runs_by_status(self, statuses: list[str]) -> list[dict]:
        """按状态列出工作流运行记录。

        Args:
            statuses: 目标状态列表。

        Returns:
            匹配状态的运行记录列表。
        """
        return list(
            self._runs.find({"status": {"$in": statuses}}).sort("created_at", 1)
        )

    def mark_run_queued(self, run_id: str) -> None:
        """将工作流运行标记为排队中。

        Args:
            run_id: 工作流运行标识。
        """
        self._runs.update_one(
            {"run_id": run_id},
            {
                "$set": {
                    "status": WorkflowRunStatus.QUEUED.value,
                    "current_step_index": 0,
                }
            },
        )

    def mark_run_started(self, run_id: str) -> None:
        """将工作流运行标记为执行中。

        Args:
            run_id: 工作流运行标识。
        """
        self._runs.update_one(
            {"run_id": run_id},
            {
                "$set": {
                    "status": WorkflowRunStatus.RUNNING.value,
                    "started_at": datetime.now(timezone.utc),
                    "finished_at": None,
                }
            },
        )

    def mark_step_running(
        self,
        run_id: str,
        step_index: int,
        current_step_index: int,
    ) -> None:
        """将指定步骤标记为执行中。

        Args:
            run_id: 工作流运行标识。
            step_index: 步骤索引。
            current_step_index: 当前执行步骤序号。
        """
        now_text = datetime.now().strftime("%Y-%m-%d %H:%M")
        self._runs.update_one(
            {"run_id": run_id},
            {
                "$set": {
                    "status": WorkflowRunStatus.RUNNING.value,
                    "current_step_index": current_step_index,
                    f"step_runs.{step_index}.status": StepRunStatus.RUNNING.value,
                    f"step_runs.{step_index}.started_at": now_text,
                    f"step_runs.{step_index}.finished_at": "",
                }
            },
        )

    def mark_step_pending(self, run_id: str, step_index: int) -> None:
        """将指定步骤重置为待执行状态。

        Args:
            run_id: 工作流运行标识。
            step_index: 步骤索引。
        """
        self._runs.update_one(
            {"run_id": run_id},
            {
                "$set": {
                    f"step_runs.{step_index}.status": StepRunStatus.PENDING.value,
                    f"step_runs.{step_index}.started_at": "",
                    f"step_runs.{step_index}.finished_at": "",
                }
            },
        )

    def mark_step_success(
        self,
        run_id: str,
        step_index: int,
        payload: dict,
    ) -> None:
        """将指定步骤标记为成功。

        Args:
            run_id: 工作流运行标识。
            step_index: 步骤索引。
            payload: 步骤执行结果。
        """
        now_text = datetime.now().strftime("%Y-%m-%d %H:%M")
        self._runs.update_one(
            {"run_id": run_id},
            {
                "$set": {
                    f"step_runs.{step_index}.status": StepRunStatus.SUCCESS.value,
                    f"step_runs.{step_index}.finished_at": now_text,
                    f"step_runs.{step_index}.result": payload,
                }
            },
        )

    def mark_step_failed(
        self,
        run_id: str,
        step_index: int,
        payload: dict,
    ) -> None:
        """将指定步骤标记为失败。

        Args:
            run_id: 工作流运行标识。
            step_index: 步骤索引。
            payload: 步骤执行结果或错误信息。
        """
        now_text = datetime.now().strftime("%Y-%m-%d %H:%M")
        self._runs.update_one(
            {"run_id": run_id},
            {
                "$set": {
                    f"step_runs.{step_index}.status": StepRunStatus.FAILED.value,
                    f"step_runs.{step_index}.finished_at": now_text,
                    f"step_runs.{step_index}.result": payload,
                }
            },
        )

    def mark_run_success(self, run_id: str, summary: dict | None = None) -> None:
        """将工作流运行标记为成功。

        Args:
            run_id: 工作流运行标识。
            summary: 执行摘要信息。
        """
        self._runs.update_one(
            {"run_id": run_id},
            {
                "$set": {
                    "status": WorkflowRunStatus.SUCCESS.value,
                    "finished_at": datetime.now(timezone.utc),
                    "summary": summary or {},
                }
            },
        )

    def mark_run_failed(self, run_id: str, summary: dict | None = None) -> None:
        """将工作流运行标记为失败。

        Args:
            run_id: 工作流运行标识。
            summary: 失败摘要信息。
        """
        self._runs.update_one(
            {"run_id": run_id},
            {
                "$set": {
                    "status": WorkflowRunStatus.FAILED.value,
                    "finished_at": datetime.now(timezone.utc),
                    "summary": summary or {},
                }
            },
        )
