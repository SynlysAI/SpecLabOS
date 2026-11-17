"""设备日志接口路由。"""

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query

from app.schemas.log import DeviceLogContentResponse, DeviceLogFileListResponse
from app.services.data_asset_service import DataAssetService

router = APIRouter(prefix="/api/logs", tags=["logs"])
DEVICE_LOG_DATA_TYPE = "device_log"


def get_data_asset_service() -> DataAssetService:
    """创建数据资产服务。"""
    return DataAssetService()


@router.get("", response_model=DeviceLogFileListResponse)
def list_logs(
    keyword: str | None = Query(default=None),
    device_id: str | None = Query(default=None),
    date: str | None = Query(default=None),
    days: int = Query(default=7, ge=0, le=3650),
    limit: int = Query(default=100, ge=1, le=500),
    service: DataAssetService = Depends(get_data_asset_service),
) -> DeviceLogFileListResponse:
    """返回数据中心日志类文件。

    Args:
        keyword: 文件名或路径关键字。
        device_id: 设备 ID。
        date: 指定日期，格式为 YYYY-MM-DD。
        days: 未指定日期时回溯的天数，0 表示不限制。
        limit: 最大返回数量。

    Returns:
        按入库时间倒序的日志文件列表。
    """
    start_at, end_at = _resolve_time_window(date, days)
    items, total = service.list_files_by_type(
        DEVICE_LOG_DATA_TYPE,
        keyword=keyword,
        device_id=device_id,
        start_at=start_at,
        end_at=end_at,
        limit=limit,
    )
    return DeviceLogFileListResponse(
        items=[_to_log_file_item(item) for item in items],
        total=total,
    )


@router.get("/{file_id}/content", response_model=DeviceLogContentResponse)
def get_log_content(
    file_id: str,
    service: DataAssetService = Depends(get_data_asset_service),
) -> DeviceLogContentResponse:
    """返回指定日志文件的文本内容。

    Args:
        file_id: 数据文件 ID。
        service: 数据资产服务。

    Returns:
        日志文件尾部文本。
    """
    return DeviceLogContentResponse.model_validate(service.read_text_file(file_id))


def _resolve_time_window(selected_date: str | None, days: int) -> tuple[str | None, str | None]:
    """解析日志查询时间窗。

    Args:
        selected_date: 指定日期。
        days: 回溯天数。

    Returns:
        入库时间上下限。
    """
    if selected_date:
        day = datetime.strptime(selected_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        return day.isoformat(), (day + timedelta(days=1)).isoformat()
    if days <= 0:
        return None, None
    start = datetime.now(timezone.utc) - timedelta(days=days)
    return start.isoformat(), None


def _to_log_file_item(item: dict) -> dict:
    """把数据文件记录转换为日志文件项。

    Args:
        item: 数据资产文件记录。

    Returns:
        日志文件列表项。
    """
    metadata = item.get("metadata") if isinstance(item.get("metadata"), dict) else {}
    return {
        "file_id": item.get("file_id", ""),
        "filename": item.get("filename", ""),
        "device_id": item.get("device_id", ""),
        "collector_id": item.get("collector_id", ""),
        "watcher_name": str(metadata.get("watcher_name") or ""),
        "relative_path": item.get("relative_path", ""),
        "content_type": item.get("content_type", ""),
        "file_size": int(item.get("file_size") or 0),
        "ingested_at": str(item.get("ingested_at") or ""),
        "created_at": str(item.get("created_at") or ""),
    }
