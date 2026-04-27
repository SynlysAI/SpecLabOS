"""工作流接口路由。"""

from fastapi import APIRouter

from app.schemas.workflow import WorkflowListResponse


router = APIRouter(prefix="/api/workflows", tags=["workflows"])


@router.get("", response_model=WorkflowListResponse)
def list_workflows() -> WorkflowListResponse:
    """返回工作流列表数据。"""
    return WorkflowListResponse(items=[])
