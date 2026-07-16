"""Raman 设备定义。"""

from typing import Any

import requests

from app.core.config import get_settings
from app.devices.registry import capability, device, local_executor
from app.domain.capability import DeviceCapability
from app.domain.device import DeviceResource


@device
class RamanDevice(DeviceResource):
    """Raman 拉曼光谱仪。"""

    device_id: str = "raman_2278"
    name: str = "raman_2278"
    category: str = "拉曼光谱仪"
    device_type: str = "RamanSpectrometer"
    location: str = "A-118"


@local_executor("raman_2278", "raman.capture")
def raman_capture_executor(
    params: dict[str, Any],
    context: dict[str, Any],
) -> dict[str, Any]:
    """下发 Raman 采集任务。

    Args:
        params: 执行参数。
        context: 运行上下文。

    Returns:
        Raman 服务响应。
    """
    return _request_raman(
        "POST",
        _get_raman_endpoint("capture"),
        "/raman/jy/capture",
        payload={
            "req_id": params.get("req_id"),
            "capture": params.get("capture", {}),
        },
    )


@local_executor("raman_2278", "raman.camera_focus")
def raman_camera_focus_executor(
    params: dict[str, Any],
    context: dict[str, Any],
) -> dict[str, Any]:
    """执行 Raman 镜头对焦。

    Args:
        params: 执行参数。
        context: 运行上下文。

    Returns:
        Raman 服务响应。
    """
    return _request_raman(
        "POST",
        _get_raman_endpoint("capture"),
        "/raman/jy/camera",
        payload={
            "rt": params.get("rt", 8000),
            "rb": params.get("rb", 5000),
            "s": params.get("s", 3),
            "method": 0,
        },
    )


@local_executor("raman_2278", "raman.get_result")
def raman_get_result_executor(
    params: dict[str, Any],
    context: dict[str, Any],
) -> dict[str, Any]:
    """查询 Raman 采集任务结果。

    Args:
        params: 执行参数。
        context: 运行上下文。

    Returns:
        Raman 服务响应。
    """
    return _request_raman(
        "GET",
        _get_raman_endpoint("result"),
        "/raman/jy/result",
        params={"req_id": params.get("req_id")},
    )


@capability("拉曼光谱仪")
def raman_capture() -> DeviceCapability:
    """下发采集任务。"""
    return DeviceCapability(
        capability_key="raman.capture",
        device_category="拉曼光谱仪",
        name="下发采集任务",
        description="向 Raman 服务下发采集任务",
        step_mode="auto",
        parameter_schema={
            "type": "object",
            "properties": {
                "req_id": {"type": "string", "description": "请求编号"},
                "capture": {"type": "object", "description": "采集任务 body 参数"},
            },
            "required": ["req_id", "capture"],
        },
    )


@capability("拉曼光谱仪")
def raman_camera_focus() -> DeviceCapability:
    """镜头对焦。"""
    return DeviceCapability(
        capability_key="raman.camera_focus",
        device_category="拉曼光谱仪",
        name="镜头对焦",
        description="自动对焦 Raman 设备镜头",
        step_mode="hidden",
        parameter_schema={
            "type": "object",
            "properties": {
                "rt": {"type": "number", "description": "上限"},
                "rb": {"type": "number", "description": "下限"},
                "s": {"type": "number", "description": "步长"},
            },
            "required": ["rt", "rb", "s"],
        },
    )


@capability("拉曼光谱仪")
def raman_get_result() -> DeviceCapability:
    """查询任务结果。"""
    return DeviceCapability(
        capability_key="raman.get_result",
        device_category="拉曼光谱仪",
        name="查询任务结果",
        description="查询 Raman 采集任务状态或结果",
        step_mode="auto",
        parameter_schema={
            "type": "object",
            "properties": {
                "req_id": {"type": "string", "description": "请求编号"},
            },
            "required": ["req_id"],
        },
    )


def _request_raman(
    method: str,
    base_url: str,
    path: str,
    payload: dict[str, Any] | None = None,
    params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """调用 Raman 远程接口。

    Args:
        method: HTTP 方法。
        base_url: 接口基础地址。
        path: 接口路径。
        payload: 请求体。
        params: 查询参数。

    Returns:
        Raman 服务响应。
    """
    response = requests.request(
        method=method,
        url=f"{base_url.rstrip('/')}{path}",
        timeout=get_settings().apis.raman.timeout,
        json=payload,
        params=params,
    )
    response.raise_for_status()
    try:
        return response.json()
    except ValueError:
        return {"raw_text": response.text}


def _get_raman_endpoint(endpoint_name: str) -> str:
    """获取 Raman 指定命名端点。

    Args:
        endpoint_name: 端点名称，支持 capture 或 result。

    Returns:
        Raman 服务基础地址。
    """
    settings = get_settings()
    config_endpoint = (
        settings.devices.items.get("raman_2278")
        and settings.devices.items["raman_2278"].endpoints.get(endpoint_name)
    )
    if config_endpoint:
        return config_endpoint
    if endpoint_name == "result":
        return settings.apis.raman.result_base_url
    return settings.apis.raman.capture_base_url
