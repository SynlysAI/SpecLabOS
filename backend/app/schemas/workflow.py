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
