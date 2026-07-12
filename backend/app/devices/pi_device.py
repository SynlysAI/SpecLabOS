"""PI 设备定义。"""

from typing import Any

import requests

from app.core.config import get_settings
from app.devices.registry import capability, device, local_executor
from app.domain.capability import DeviceCapability
from app.domain.device import DeviceResource


@device
class PIDevice(DeviceResource):
    """PI 合成系统。"""

    device_id: str = "pi_2278"
    name: str = "pi_2278"
    category: str = "PI 合成系统"
    device_type: str = "PISynthesisSystem"
    location: str = "A-301"


@local_executor("pi_2278", "pi.health_check")
def pi_health_check_executor(
    params: dict[str, Any],
    context: dict[str, Any],
) -> dict[str, Any]:
    """执行 PI 健康检查。

    Args:
        params: 执行参数。
        context: 运行上下文。

    Returns:
        PI 服务响应。
    """
    return _request_pi("GET", "/health")


@local_executor("pi_2278", "pi.power_on")
def pi_power_on_executor(
    params: dict[str, Any],
    context: dict[str, Any],
) -> dict[str, Any]:
    """执行 PI 启动。

    Args:
        params: 执行参数。
        context: 运行上下文。

    Returns:
        PI 服务响应。
    """
    return _request_pi("POST", "/ui/start")


@local_executor("pi_2278", "pi.pause")
def pi_pause_executor(
    params: dict[str, Any],
    context: dict[str, Any],
) -> dict[str, Any]:
    """执行 PI 暂停。

    Args:
        params: 执行参数。
        context: 运行上下文。

    Returns:
        PI 服务响应。
    """
    return _request_pi("POST", "/ui/pause")


@local_executor("pi_2278", "pi.power_off")
def pi_power_off_executor(
    params: dict[str, Any],
    context: dict[str, Any],
) -> dict[str, Any]:
    """执行 PI 停止。

    Args:
        params: 执行参数。
        context: 运行上下文。

    Returns:
        PI 服务响应。
    """
    return _request_pi("POST", "/ui/stop")


@capability("PI 合成系统")
def pi_health_check() -> DeviceCapability:
    """健康检查。"""
    return DeviceCapability(
        capability_key="pi.health_check",
        device_category="PI 合成系统",
        name="健康检查",
        description="检查 PI 服务健康状态",
        step_mode="auto",
    )


@capability("PI 合成系统")
def pi_power_on() -> DeviceCapability:
    """启动。"""
    return DeviceCapability(
        capability_key="pi.power_on",
        device_category="PI 合成系统",
        name="启动",
        description="触发 PI 启动按钮",
        step_mode="auto",
    )


@capability("PI 合成系统")
def pi_pause() -> DeviceCapability:
    """暂停。"""
    return DeviceCapability(
        capability_key="pi.pause",
        device_category="PI 合成系统",
        name="暂停",
        description="触发 PI 暂停按钮",
        step_mode="auto",
    )


@capability("PI 合成系统")
def pi_power_off() -> DeviceCapability:
    """停止。"""
    return DeviceCapability(
        capability_key="pi.power_off",
        device_category="PI 合成系统",
        name="停止",
        description="触发 PI 停止按钮",
        step_mode="auto",
    )


def _request_pi(method: str, path: str) -> dict[str, Any]:
    """调用 PI 远程接口。

    Args:
        method: HTTP 方法。
        path: 接口路径。

    Returns:
        PI 服务响应。
    """
    settings = get_settings()
    base_url = settings.apis.pi.base_url.rstrip("/")
    response = requests.request(
        method=method,
        url=f"{base_url}{path}",
        timeout=settings.apis.pi.timeout,
    )
    response.raise_for_status()
    return response.json()
