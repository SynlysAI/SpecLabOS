"""日志接口路由。"""

from fastapi import APIRouter

from app.schemas.log import LogListResponse


router = APIRouter(prefix="/api/logs", tags=["logs"])


@router.get("", response_model=LogListResponse)
def list_logs() -> LogListResponse:
    """返回日志列表数据。"""
    return LogListResponse(items=[])
