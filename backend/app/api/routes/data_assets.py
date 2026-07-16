"""SmartDataHub 数据资产接口。"""

from fastapi import APIRouter, Depends, File, Form, Header, HTTPException, Query, UploadFile, status

from app.core.auth import parse_access_token
from app.core.config import get_settings
from app.schemas.data_assets import (
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
    if not authorization:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="未提供认证信息。")

    api_token = get_settings().datahub.api_token
    if api_token and authorization == f"Bearer {api_token}":
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


@router.get("/assets", response_model=DataAssetListResponse)
def list_assets(
    limit: int = Query(default=50, ge=1, le=500),
    keyword: str | None = Query(default=None),
    device_id: str | None = Query(default=None),
    collector_id: str | None = Query(default=None),
    data_type: str | None = Query(default=None),
) -> DataAssetListResponse:
    """查询数据资产列表。

    Args:
        limit: 最大返回数量。
        keyword: 关键词，匹配资产名、文件名或资产组。
        device_id: 设备 ID。
        collector_id: 采集器 ID。
        data_type: 数据类型。

    Returns:
        数据资产列表和匹配总数。
    """
    items, total = DataAssetService().list_assets(
        limit=limit,
        keyword=keyword,
        device_id=device_id,
        collector_id=collector_id,
        data_type=data_type,
    )
    return DataAssetListResponse(items=items, total=total)


@router.get("/assets/{asset_id}/files", response_model=DataAssetFileListResponse)
def list_asset_files(
    asset_id: str,
    limit: int = Query(default=200, ge=1, le=2000),
) -> DataAssetFileListResponse:
    """查询指定资产的文件明细。"""
    items = DataAssetService().list_files(asset_id=asset_id, limit=limit)
    return DataAssetFileListResponse(items=items)
