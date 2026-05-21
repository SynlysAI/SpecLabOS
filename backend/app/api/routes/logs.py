"""日志接口路由。"""

from fastapi import APIRouter, Query

from app.core.config import get_settings
from app.schemas.log import AutomationRateSummaryResponse, LogListResponse
from app.services.log_service import DeviceLogService


router = APIRouter(prefix="/api/logs", tags=["logs"])


@router.get("", response_model=LogListResponse)
def list_logs(
    keyword: str | None = Query(default=None),
    level: str | None = Query(default=None),
    source: str | None = Query(default=None),
    date: str | None = Query(default=None),
) -> LogListResponse:
    """返回日志列表数据。"""
    service = DeviceLogService(get_settings().device_logs)
    filtered_items = service.list_logs(
        keyword=keyword,
        level=level,
        source=source,
        selected_date=date,
    )
    return LogListResponse(items=filtered_items)


@router.get("/automation-rate", response_model=AutomationRateSummaryResponse)
def get_automation_rate_summary() -> AutomationRateSummaryResponse:
    """返回设备日志页所需的自动化率摘要。"""
    service = DeviceLogService(get_settings().device_logs)
    return AutomationRateSummaryResponse.model_validate(
        service.get_automation_rate_summary()
    )
