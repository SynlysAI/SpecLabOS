"""SmartDataHub 数据资产接口。"""

from fastapi import APIRouter, Depends, File, Form, Header, HTTPException, Query, UploadFile, status

from app.core.auth import get_current_user_optional, parse_access_token
from app.core.config import get_settings
from app.schemas.data_assets import (
    DataAssetFileListResponse,
    DataAssetListResponse,
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


@router.get("/assets", response_model=DataAssetListResponse)
def list_assets(limit: int = Query(default=50, ge=1, le=500)) -> DataAssetListResponse:
    """查询数据资产列表。"""
    items = DataAssetService().list_assets(limit=limit)
    return DataAssetListResponse(items=items)


@router.get("/assets/{asset_id}/files", response_model=DataAssetFileListResponse)
def list_asset_files(
    asset_id: str,
    limit: int = Query(default=200, ge=1, le=2000),
) -> DataAssetFileListResponse:
    """查询指定资产的文件明细。"""
    items = DataAssetService().list_files(asset_id=asset_id, limit=limit)
    return DataAssetFileListResponse(items=items)
