"""SmartDataHub 数据资产接口。"""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, File, Form, Header, HTTPException, Query, UploadFile, status

from app.core.auth import parse_access_token
from app.core.config import get_settings
from app.schemas.data_assets import (
    DataAssetDeviceStatsResponse,
    DataAssetFileListResponse,
    DataAssetListResponse,
    DataAssetOverviewResponse,
    DataIngestFileResponse,
)
from app.services.data_asset_service import DataAssetService


def require_datahub_auth(authorization: str | None = Header(default=None)) -> None:
    """校验 SmartDataHub 上传接口认证。

    Args:
        authorization: HTTP Authorization 请求头。
    """
    if not get_settings().auth.enabled:
        return

    if not authorization:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="未提供认证信息。")

    api_token = get_settings().datahub.api_token
    unified_token = get_settings().external_api.api_token
    for accepted_token in (api_token, unified_token):
        if accepted_token and authorization == f"Bearer {accepted_token}":
            return

    token = authorization[7:] if authorization.startswith("Bearer ") else None
    if token and parse_access_token(token):
        return

    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="认证信息无效。")


router = APIRouter(
    prefix="/api/data",
    tags=["data"],
    dependencies=[Depends(require_datahub_auth)],
)


@router.post("/ingest/files", response_model=DataIngestFileResponse)
def ingest_file(
    file: UploadFile = File(...),
    metadata: str = Form(...),
) -> DataIngestFileResponse:
    """接收单个文件并上传到 MinIO。"""
    record = DataAssetService().ingest_file(file, metadata)
    return DataIngestFileResponse(
        asset_id=record["asset_id"],
        file_id=record["file_id"],
        storage_bucket=record["storage_bucket"],
        storage_key=record["storage_key"],
        storage_uri=record["storage_uri"],
        upload_status=record["upload_status"],
    )


@router.get("/overview", response_model=DataAssetOverviewResponse)
def get_overview() -> DataAssetOverviewResponse:
    """查询 SmartDataHub 数据资产概览。

    Returns:
        数据资产全量统计与分布信息。
    """
    return DataAssetOverviewResponse(**DataAssetService().get_overview())


def _parse_ingested_bound(value: str | None, field: str) -> datetime | None:
    """解析入库时间边界参数为规范化 UTC 时间。

    Args:
        value: ISO 8601 时间字符串，可为空。
        field: 参数名，用于错误提示。

    Returns:
        UTC 时间对象；参数为空时返回 None。

    Raises:
        HTTPException: 时间格式不合法时抛出 400。
    """
    if value is None or value == "":
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{field} 不是合法的 ISO 8601 时间。",
        ) from error
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


@router.get("/assets", response_model=DataAssetListResponse)
def list_assets(
    limit: int = Query(default=50, ge=1, le=500),
    keyword: str | None = Query(default=None),
    device_id: str | None = Query(default=None),
    collector_id: str | None = Query(default=None),
    data_type: str | None = Query(default=None),
    asset_kind: str | None = Query(default=None),
    ingested_start: str | None = Query(default=None),
    ingested_end: str | None = Query(default=None),
) -> DataAssetListResponse:
    """查询数据资产列表。

    Args:
        limit: 最大返回数量。
        keyword: 关键词，匹配资产名、文件名或资产组。
        device_id: 设备 ID。
        collector_id: 采集器 ID。
        data_type: 数据类型。
        asset_kind: 资产类型，文件或目录。
        ingested_start: 入库时间下界（ISO 8601，含）。
        ingested_end: 入库时间上界（ISO 8601，含）。

    Returns:
        数据资产列表和匹配总数。
    """
    items, total = DataAssetService().list_assets(
        limit=limit,
        keyword=keyword,
        device_id=device_id,
        collector_id=collector_id,
        data_type=data_type,
        asset_kind=asset_kind,
        ingested_start=_parse_ingested_bound(ingested_start, "ingested_start"),
        ingested_end=_parse_ingested_bound(ingested_end, "ingested_end"),
    )
    return DataAssetListResponse(items=items, total=total)


@router.get("/device-stats", response_model=DataAssetDeviceStatsResponse)
def get_device_stats() -> DataAssetDeviceStatsResponse:
    """查询 SmartDataHub 按设备聚合的数据资产统计。"""
    return DataAssetDeviceStatsResponse(**DataAssetService().get_device_stats())


@router.get("/files", response_model=DataAssetFileListResponse)
def list_files_in_window(
    device_id: str = Query(min_length=1),
    ingested_start: str = Query(min_length=1),
    ingested_end: str = Query(min_length=1),
    limit: int = Query(default=200, ge=1, le=2000),
) -> DataAssetFileListResponse:
    """查询设备在入库时间窗内的数据文件。"""
    items = DataAssetService().list_files_in_window(
        device_id=device_id,
        start_at=_parse_ingested_bound(ingested_start, "ingested_start"),
        end_at=_parse_ingested_bound(ingested_end, "ingested_end"),
        limit=limit,
    )
    return DataAssetFileListResponse(items=items)


@router.get("/assets/{asset_id}/files", response_model=DataAssetFileListResponse)
def list_asset_files(
    asset_id: str,
    limit: int = Query(default=200, ge=1, le=2000),
) -> DataAssetFileListResponse:
    """查询指定资产的文件明细。"""
    items = DataAssetService().list_files(asset_id=asset_id, limit=limit)
    return DataAssetFileListResponse(items=items)
