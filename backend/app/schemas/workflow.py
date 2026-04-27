"""工作流相关 Schema。"""

from pydantic import BaseModel, Field


class WorkflowItem(BaseModel):
    """工作流列表项。"""

    workflow_id: str
    name: str
    status: str = "pending"


class WorkflowListResponse(BaseModel):
    """工作流列表响应。"""

    items: list[WorkflowItem] = Field(default_factory=list)


class WorkflowRunItem(BaseModel):
    """工作流运行列表项。"""

    run_id: str
    workflow_name: str
    status: str = "pending"
    current_step_index: int = 0
    total_steps: int = 0
    started_at: str = "--"


class WorkflowRunListResponse(BaseModel):
    """工作流运行列表响应。"""

    items: list[WorkflowRunItem] = Field(default_factory=list)


class WorkflowRunStepItem(BaseModel):
    """工作流运行步骤项。"""

    name: str
    status: str = "idle"
    started_at: str = ""
    finished_at: str = ""
    description: str = ""


class WorkflowRunDetailResponse(BaseModel):
    """工作流运行详情响应。"""

    run_id: str
    workflow_name: str
    status: str = "pending"
    current_step_index: int = 0
    total_steps: int = 0
    started_at: str = "--"
    finished_at: str = ""
    trigger_source: str = "manual"
    operator_name: str = "system"
    steps: list[WorkflowRunStepItem] = Field(default_factory=list)
