"""设备接口路由。"""

from fastapi import APIRouter

from app.schemas.device import DeviceListResponse


router = APIRouter(prefix="/api/devices", tags=["devices"])


@router.get("", response_model=DeviceListResponse)
def list_devices() -> DeviceListResponse:
    """返回设备列表数据。"""
    return DeviceListResponse(items=[])
