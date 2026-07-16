"""设备接口路由。"""

from pathlib import Path

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse

from app.core.config import get_settings
from app.devices.raman_device import _get_raman_endpoint, _request_raman
from app.runtime import get_device_service, get_device_status_service
from app.schemas.device import (
    CameraFocusRequest,
    DeviceActionField,
    DeviceActionItem,
    DeviceActionListResponse,
    DeviceItem,
    DeviceListResponse,
)


router = APIRouter(prefix="/api/devices", tags=["devices"])
device_images_router = APIRouter(prefix="/api/device-images", tags=["device-images"])

_SUPPORTED_EXTENSIONS = (".jpg", ".jpeg", ".png", ".webp", ".gif")


def _find_device_image(device_type: str) -> Path | None:
    """按设备类型查找图片文件。"""
    image_dir = Path(get_settings().device_images.image_dir)
    direct_candidate = image_dir / device_type
    if direct_candidate.suffix.lower() in _SUPPORTED_EXTENSIONS and direct_candidate.is_file():
        return direct_candidate
    for extension in _SUPPORTED_EXTENSIONS:
        candidate = image_dir / f"{device_type}{extension}"
        if candidate.is_file():
            return candidate
    return None


@router.get("", response_model=DeviceListResponse)
def list_devices(
    refresh_status: bool = Query(default=False),
    include_smartaccess: bool = Query(default=True),
) -> DeviceListResponse:
    """返回设备列表数据。"""
    device_service = get_device_service()
    devices = device_service.list_devices(include_smartaccess=include_smartaccess)
    if refresh_status:
        get_device_status_service().refresh_devices(devices)
    items = []
    for device in devices:
        serialized_device = device_service.serialize_device(device)
        if not serialized_device.get("image_url") and _find_device_image(serialized_device["device_type"]) is not None:
            serialized_device["image_url"] = (
                f"/api/device-images/{serialized_device['device_type']}"
            )
        items.append(DeviceItem(**serialized_device))
    return DeviceListResponse(items=items)


@router.get("/{device_key}", response_model=DeviceItem)
def get_device_detail(device_key: str) -> DeviceItem:
    """返回单个设备详情。"""
    device_service = get_device_service()
    device = device_service.get_device(device_key)
    if device is None:
        raise HTTPException(status_code=404, detail="设备不存在")
    serialized_device = device_service.serialize_device(device)
    if not serialized_device.get("image_url") and _find_device_image(serialized_device["device_type"]) is not None:
        serialized_device["image_url"] = (
            f"/api/device-images/{serialized_device['device_type']}"
        )
    return DeviceItem(**serialized_device)


@router.post("/{device_key}/refresh-status", response_model=DeviceItem)
def refresh_device_status(device_key: str) -> DeviceItem:
    """刷新并返回单个设备状态。"""
    device_service = get_device_service()
    device = device_service.get_device(device_key)
    if device is None:
        raise HTTPException(status_code=404, detail="设备不存在")
    get_device_status_service().refresh_device(device)
    serialized_device = device_service.serialize_device(device)
    if not serialized_device.get("image_url") and _find_device_image(serialized_device["device_type"]) is not None:
        serialized_device["image_url"] = (
            f"/api/device-images/{serialized_device['device_type']}"
        )
    return DeviceItem(**serialized_device)


@router.get("/{device_key}/actions", response_model=DeviceActionListResponse)
def list_device_actions(device_key: str) -> DeviceActionListResponse:
    """返回指定设备支持的动作声明。"""
    device_service = get_device_service()
    device = device_service.get_device(device_key)
    if device is None:
        raise HTTPException(status_code=404, detail="设备不存在")
    items = []
    for action in device_service.list_actions(device_key):
        serialized_action = device_service.serialize_action(action)
        items.append(
            DeviceActionItem(
                action_key=serialized_action["action_key"],
                name=serialized_action["name"],
                description=serialized_action["description"],
                step_mode=serialized_action["step_mode"],
                parameter_schema=[
                    DeviceActionField(**field)
                    for field in serialized_action["parameter_schema"]
                ],
            )
        )
    return DeviceActionListResponse(items=items)


@router.post("/{device_key}/camera-focus")
def execute_camera_focus(device_key: str, payload: CameraFocusRequest):
    """执行 Raman 设备镜头自动对焦。"""
    settings = get_settings()
    try:
        return _request_raman(
            "POST",
            _get_raman_endpoint("capture"),
            "/raman/jy/camera",
            payload={
                "rt": payload.rt,
                "rb": payload.rb,
                "s": payload.s,
                "method": 0,
            },
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"镜头对焦请求失败: {exc}")


@device_images_router.get("/{device_type}")
def get_device_image(device_type: str):
    """返回指定设备类型的图片资源。"""
    image_path = _find_device_image(device_type)
    if image_path is None:
        raise HTTPException(status_code=404, detail="设备图片不存在")
    return FileResponse(path=image_path)
