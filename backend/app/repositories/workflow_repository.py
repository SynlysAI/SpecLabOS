"""工作流仓储实现。"""

from datetime import datetime, timezone
from uuid import uuid4

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
