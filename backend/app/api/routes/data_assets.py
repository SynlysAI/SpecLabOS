"""SmartDataHub 数据资产接口。"""

import os
from datetime import datetime, timezone
from urllib.parse import quote

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, Header, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse, StreamingResponse

from app.api.external_auth import caller_user
from app.core.auth import parse_access_token
from app.core.config import get_settings
from app.runtime import get_device_permission_service
from app.schemas.data_assets import (
    DataAssetDeviceStatsResponse,
    DataAssetFileListResponse,
    DataAssetListResponse,
    DataAssetOverviewResponse,
    DataIngestFileResponse,
)
from app.services.data_asset_service import DataAssetService
from app.services.device_permission_service import DevicePermissionService


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


def _get_permission_service() -> DevicePermissionService:
    """获取设备权限服务单例。"""
    return get_device_permission_service()


def _mark_deletable(
    items: list[dict],
    user: dict | None,
    permission_service: DevicePermissionService,
) -> list[dict]:
    """为文件或资产记录列表标记当前用户是否可删除。

    管理员或对记录所属设备有编辑(control)权限的用户可删除。

    Args:
        items: 文件或资产记录列表。
        user: 当前用户文档，匿名或服务主体时为 None。
        permission_service: 设备权限服务实例。

    Returns:
        附加 can_delete 标记后的记录列表。
    """
    if permission_service.is_admin(user):
        allowed_keys: set[str] | None = None
    elif user:
        allowed_keys = set(permission_service.list_user_device_keys(user))
    else:
        allowed_keys = set()
    for item in items:
        device_id = str(item.get("device_id") or "")
        item["can_delete"] = allowed_keys is None or device_id in allowed_keys
    return items


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
    user: dict | None = Depends(caller_user),
    permission_service: DevicePermissionService = Depends(_get_permission_service),
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
        user: 当前用户文档，用于计算删除权限。
        permission_service: 设备权限服务实例。

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
    return DataAssetListResponse(
        items=_mark_deletable(items, user, permission_service),
        total=total,
    )


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
    user: dict | None = Depends(caller_user),
    permission_service: DevicePermissionService = Depends(_get_permission_service),
) -> DataAssetFileListResponse:
    """查询设备在入库时间窗内的数据文件。"""
    items = DataAssetService().list_files_in_window(
        device_id=device_id,
        start_at=_parse_ingested_bound(ingested_start, "ingested_start"),
        end_at=_parse_ingested_bound(ingested_end, "ingested_end"),
        limit=limit,
    )
    return DataAssetFileListResponse(items=_mark_deletable(items, user, permission_service))


@router.get("/files/{file_id}/download")
def download_file(file_id: str):
    """以附件形式下载指定数据文件。"""
    stream, filename, content_type, file_size = DataAssetService().open_file_stream(file_id)
    headers = {
        "Content-Disposition": f"attachment; filename*=UTF-8''{quote(filename)}",
    }
    if file_size > 0:
        headers["Content-Length"] = str(file_size)
    return StreamingResponse(
        stream,
        media_type=content_type,
        headers=headers,
    )


@router.get("/assets/{asset_id}/files", response_model=DataAssetFileListResponse)
def list_asset_files(
    asset_id: str,
    limit: int = Query(default=200, ge=1, le=2000),
    user: dict | None = Depends(caller_user),
    permission_service: DevicePermissionService = Depends(_get_permission_service),
) -> DataAssetFileListResponse:
    """查询指定资产的文件明细。"""
    items = DataAssetService().list_files(asset_id=asset_id, limit=limit)
    return DataAssetFileListResponse(items=_mark_deletable(items, user, permission_service))


@router.get("/assets/{asset_id}/download")
def download_data_asset(
    asset_id: str,
    background_tasks: BackgroundTasks,
):
    """下载资产文件，资产下只有一个文件时直接返回原文件，否则打包为 zip。

    Args:
        asset_id: 数据资产 ID。
        background_tasks: 响应完成后清理临时文件的背景任务。

    Returns:
        原文件流或 zip 压缩包响应。

    Raises:
        HTTPException: 资产不存在、没有文件或打包失败。
    """
    service = DataAssetService()
    record = service.get_asset_record(asset_id)
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="数据资产不存在")

    files = service.list_files(asset_id, limit=2)
    if len(files) == 1:
        stream, filename, content_type, file_size = service.open_file_stream(files[0]["file_id"])
        headers = {
            "Content-Disposition": f"attachment; filename*=UTF-8''{quote(filename)}",
        }
        if file_size > 0:
            headers["Content-Length"] = str(file_size)
        return StreamingResponse(stream, media_type=content_type, headers=headers)

    zip_name = f"{str(record.get('root_name') or record.get('filename') or record.get('asset_group_id') or asset_id)}.zip"
    temp_path = service.pack_asset_to_zip(asset_id)
    background_tasks.add_task(_remove_temp_file, temp_path)
    return FileResponse(temp_path, media_type="application/zip", filename=zip_name)


@router.delete("/files/{file_id}")
def delete_data_file(
    file_id: str,
    user: dict | None = Depends(caller_user),
    permission_service: DevicePermissionService = Depends(_get_permission_service),
) -> dict:
    """删除单个数据文件及其存储对象。

    管理员或对文件所属设备有编辑(control)权限的用户可删除。

    Args:
        file_id: 数据文件 ID。
        user: 当前用户文档。
        permission_service: 设备权限服务实例。

    Returns:
        删除摘要信息。

    Raises:
        HTTPException: 文件不存在或没有删除权限。
    """
    service = DataAssetService()
    record = service.get_file_record(file_id)
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="数据文件不存在")
    if user is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="没有删除该文件的权限")
    permission_service.assert_control(user, [str(record.get("device_id") or "")])
    return service.delete_file(file_id)


@router.delete("/assets/{asset_id}")
def delete_data_asset(
    asset_id: str,
    user: dict | None = Depends(caller_user),
    permission_service: DevicePermissionService = Depends(_get_permission_service),
) -> dict:
    """删除整个数据资产及其全部文件与存储对象。

    管理员或对资产所属设备有编辑(control)权限的用户可删除。

    Args:
        asset_id: 数据资产 ID。
        user: 当前用户文档。
        permission_service: 设备权限服务实例。

    Returns:
        删除摘要信息。

    Raises:
        HTTPException: 资产不存在或没有删除权限。
    """
    service = DataAssetService()
    record = service.get_asset_record(asset_id)
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="数据资产不存在")
    if user is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="没有删除该资产的权限")
    permission_service.assert_control(user, [str(record.get("device_id") or "")])
    return service.delete_asset(asset_id)


def _remove_temp_file(path: str) -> None:
    """删除资产打包产生的临时 zip 文件。

    Args:
        path: 临时文件路径。
    """
    try:
        os.remove(path)
    except OSError:
        pass
