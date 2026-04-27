"""领域模型定义。"""

from datetime import datetime, timezone
from uuid import uuid4

from pydantic import BaseModel, Field

from app.domain.enums import StepRunStatus, WorkflowRunStatus


class WorkflowStepDefinition(BaseModel):
    """工作流步骤定义。"""

    step_id: str
    device_key: str
    action_key: str
    params: dict = Field(default_factory=dict)
    confirm_params: dict = Field(default_factory=dict)
    display_name: str


class WorkflowDefinitionCreate(BaseModel):
    """创建工作流定义时使用的数据。"""

    name: str
    description: str = ""
    source: str = "manual"
    steps: list[WorkflowStepDefinition]
    tags: list[str] = Field(default_factory=list)
    created_by: str = "system"


class WorkflowDefinitionRecord(WorkflowDefinitionCreate):
    """持久化后的工作流定义记录。"""

    workflow_id: str
    created_at: datetime


class WorkflowStepRunRecord(BaseModel):
    """工作流步骤运行记录。"""

    step_id: str
    device_key: str
    action_key: str
    display_name: str
    status: StepRunStatus = StepRunStatus.PENDING
    params: dict = Field(default_factory=dict)
    confirm_params: dict = Field(default_factory=dict)


class WorkflowRunRecord(BaseModel):
    """工作流运行记录。"""

    run_id: str
    workflow_id: str
    workflow_name: str
    status: WorkflowRunStatus
    current_step_index: int
    total_steps: int
    step_runs: list[WorkflowStepRunRecord] = Field(default_factory=list)
    started_at: datetime | None = None
    finished_at: datetime | None = None
    created_at: datetime
    created_by: str
    trigger_source: str = "manual"
    summary: dict = Field(default_factory=dict)

    @staticmethod
    def from_definition(
        definition: WorkflowDefinitionRecord,
    ) -> "WorkflowRunRecord":
        """根据工作流定义构造初始运行记录。

        Args:
            definition: 已持久化的工作流定义。

        Returns:
            初始状态的工作流运行记录。
        """
        step_runs = [
            WorkflowStepRunRecord(
                step_id=step.step_id,
                device_key=step.device_key,
                action_key=step.action_key,
                display_name=step.display_name,
                params=step.params,
                confirm_params=step.confirm_params,
            )
            for step in definition.steps
        ]
        return WorkflowRunRecord(
            run_id=str(uuid4()),
            workflow_id=definition.workflow_id,
            workflow_name=definition.name,
            status=WorkflowRunStatus.PENDING,
            current_step_index=0,
            total_steps=len(definition.steps),
            step_runs=step_runs,
            created_at=datetime.now(timezone.utc),
            created_by=definition.created_by,
            trigger_source=definition.source,
        )
