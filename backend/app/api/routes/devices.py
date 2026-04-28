"""设备接口路由。"""

from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.devices.factories import build_default_devices
from app.devices.registry import DeviceRegistry
from app.schemas.device import (
    DeviceActionField,
    DeviceActionItem,
    DeviceActionListResponse,
    DeviceItem,
    DeviceListResponse,
)
from app.services.device_service import DeviceService


router = APIRouter(prefix="/api/devices", tags=["devices"])
device_images_router = APIRouter(prefix="/api/device-images", tags=["device-images"])

_IMAGE_DIR = Path(
    r"E:\github_project\SpecLabOS\examples\spectrum_alab\alabos_project\images"
)
_SUPPORTED_EXTENSIONS = (".jpg", ".jpeg", ".png", ".webp", ".gif")


def _build_device_service() -> DeviceService:
    """构建默认设备服务。"""
    registry = DeviceRegistry()
    for device in build_default_devices():
        registry.register(device)
    return DeviceService(registry)


def _find_device_image(device_type: str) -> Path | None:
    """按设备类型查找图片文件。"""
    for extension in _SUPPORTED_EXTENSIONS:
        candidate = _IMAGE_DIR / f"{device_type}{extension}"
        if candidate.is_file():
            return candidate
    return None


@router.get("", response_model=DeviceListResponse)
def list_devices() -> DeviceListResponse:
    """返回设备列表数据。"""
    device_service = _build_device_service()
    items = []
    for device in device_service.list_devices():
        serialized_device = device_service.serialize_device(device)
        if _find_device_image(serialized_device["device_type"]) is not None:
            serialized_device["image_url"] = (
                f"/api/device-images/{serialized_device['device_type']}"
            )
        items.append(DeviceItem(**serialized_device))
    return DeviceListResponse(items=items)


@router.get("/{device_key}", response_model=DeviceItem)
def get_device_detail(device_key: str) -> DeviceItem:
    """返回单个设备详情。"""
    device_service = _build_device_service()
    for device in device_service.list_devices():
        if device.key != device_key:
            continue
        serialized_device = device_service.serialize_device(device)
        if _find_device_image(serialized_device["device_type"]) is not None:
            serialized_device["image_url"] = (
                f"/api/device-images/{serialized_device['device_type']}"
            )
        return DeviceItem(**serialized_device)
    raise HTTPException(status_code=404, detail="设备不存在")


@router.get("/{device_key}/actions", response_model=DeviceActionListResponse)
def list_device_actions(device_key: str) -> DeviceActionListResponse:
    """返回指定设备支持的动作声明。"""
    device_service = _build_device_service()
    for device in device_service.list_devices():
        if device.key != device_key:
            continue
        items = []
        for action in device.list_actions():
            items.append(
                DeviceActionItem(
                    action_key=action.action_key,
                    name=action.name,
                    description=action.description,
                    step_mode=action.step_mode,
                    parameter_schema=[
                        DeviceActionField(**field) for field in action.parameter_schema
                    ],
                )
            )
        return DeviceActionListResponse(items=items)
    raise HTTPException(status_code=404, detail="设备不存在")


@device_images_router.get("/{device_type}")
def get_device_image(device_type: str):
    """返回指定设备类型的图片资源。"""
    image_path = _find_device_image(device_type)
    if image_path is None:
        raise HTTPException(status_code=404, detail="设备图片不存在")
    return FileResponse(path=image_path)
