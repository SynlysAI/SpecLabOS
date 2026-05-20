"""日志接口路由。"""

from fastapi import APIRouter, Query

from app.core.config import get_settings
from app.schemas.log import AutomationRateSummaryResponse, LogListResponse
from app.services.log_service import DeviceLogService


router = APIRouter(prefix="/api/logs", tags=["logs"])


FALLBACK_LOG_ITEMS = [
    {
        "id": "LOG-001",
        "level": "warning",
        "source": "system",
        "service_name": "workflow-engine",
        "message": "步骤三执行超时，系统已发起重试。",
        "created_at": "2026-04-27 11:06",
    },
    {
        "id": "LOG-002",
        "level": "online",
        "source": "system",
        "service_name": "device-gateway",
        "message": "LC-MS-02 心跳恢复正常。",
        "created_at": "2026-04-27 10:58",
    },
]


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
    if not filtered_items:
        filtered_items = FALLBACK_LOG_ITEMS
        if keyword:
            filtered_items = [
                item for item in filtered_items if keyword.lower() in item["message"].lower()
            ]
        if level:
            filtered_items = [item for item in filtered_items if item["level"] == level]
        if source:
            filtered_items = [item for item in filtered_items if item["source"] == source]
    return LogListResponse(items=filtered_items)


@router.get("/automation-rate", response_model=AutomationRateSummaryResponse)
def get_automation_rate_summary() -> AutomationRateSummaryResponse:
    """返回设备日志页所需的自动化率摘要。"""
    service = DeviceLogService(get_settings().device_logs)
    return AutomationRateSummaryResponse.model_validate(
        service.get_automation_rate_summary()
    )
