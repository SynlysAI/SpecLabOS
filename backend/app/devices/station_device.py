"""工位设备定义。"""

from typing import Any

import requests

from app.core.config import get_settings
from app.devices.registry import capability, device, local_executor
from app.domain.capability import DeviceCapability
from app.domain.device import DeviceResource


@device
class MetalCoatingDevice(DeviceResource):
    """金属镀膜设备。"""

    device_id: str = "metal_108"
    name: str = "metal_108"
    category: str = "金属镀膜设备"
    device_type: str = "MetalCoatingDevice"
    location: str = "C-108"


@device
class AdhesionTestingDevice(DeviceResource):
    """附着力测试设备。"""

    device_id: str = "cat_108"
    name: str = "cat_108"
    category: str = "附着力测试设备"
    device_type: str = "AdhesionTestingDevice"
    location: str = "C-109"


@device
class MicroCharacterizationDevice(DeviceResource):
    """微观表征设备。"""

    device_id: str = "micro_108"
    name: str = "micro_108"
    category: str = "微观表征设备"
    device_type: str = "MicroCharacterizationDevice"
    location: str = "C-110"


_STATION_ACTION_KEYS = {
    "metal_108": "metal",
    "cat_108": "cat",
    "micro_108": "micro",
}

for _station_device_id, _station_action_key in _STATION_ACTION_KEYS.items():

    @local_executor(_station_device_id, f"{_station_device_id}.check_status")
    def station_check_status_executor(
        params: dict[str, Any],
        context: dict[str, Any],
        action_key: str = _station_action_key,
    ) -> dict[str, Any]:
        """查询工位设备状态。

        Args:
            params: 执行参数。
            context: 运行上下文。
            action_key: 工位动作前缀。

        Returns:
            Station 服务响应。
        """
        return _request_station(action_key, timeout=params.get("timeout"))

    @local_executor(_station_device_id, f"{_station_device_id}.power_on")
    def station_power_on_executor(
        params: dict[str, Any],
        context: dict[str, Any],
        action_key: str = _station_action_key,
    ) -> dict[str, Any]:
        """启动工位设备。

        Args:
            params: 执行参数。
            context: 运行上下文。
            action_key: 工位动作前缀。

        Returns:
            Station 服务响应。
        """
        return _request_station(action_key, "启动")

    @local_executor(_station_device_id, f"{_station_device_id}.power_off")
    def station_power_off_executor(
        params: dict[str, Any],
        context: dict[str, Any],
        action_key: str = _station_action_key,
    ) -> dict[str, Any]:
        """停止工位设备。

        Args:
            params: 执行参数。
            context: 运行上下文。
            action_key: 工位动作前缀。

        Returns:
            Station 服务响应。
        """
        return _request_station(action_key, "停止")


@capability("金属镀膜设备")
def metal_check_status() -> DeviceCapability:
    """检查状态。"""
    return DeviceCapability(
        capability_key="metal_108.check_status",
        device_category="金属镀膜设备",
        name="检查状态",
        description="查询 metal_108 当前状态",
        step_mode="auto",
    )


@capability("金属镀膜设备")
def metal_power_on() -> DeviceCapability:
    """启动。"""
    return DeviceCapability(
        capability_key="metal_108.power_on",
        device_category="金属镀膜设备",
        name="启动",
        description="启动 metal_108",
        step_mode="auto",
    )


@capability("金属镀膜设备")
def metal_power_off() -> DeviceCapability:
    """停止。"""
    return DeviceCapability(
        capability_key="metal_108.power_off",
        device_category="金属镀膜设备",
        name="停止",
        description="停止 metal_108",
        step_mode="auto",
    )


@capability("附着力测试设备")
def cat_check_status() -> DeviceCapability:
    """检查状态。"""
    return DeviceCapability(
        capability_key="cat_108.check_status",
        device_category="附着力测试设备",
        name="检查状态",
        description="查询 cat_108 当前状态",
        step_mode="auto",
    )


@capability("附着力测试设备")
def cat_power_on() -> DeviceCapability:
    """启动。"""
    return DeviceCapability(
        capability_key="cat_108.power_on",
        device_category="附着力测试设备",
        name="启动",
        description="启动 cat_108",
        step_mode="auto",
    )


@capability("附着力测试设备")
def cat_power_off() -> DeviceCapability:
    """停止。"""
    return DeviceCapability(
        capability_key="cat_108.power_off",
        device_category="附着力测试设备",
        name="停止",
        description="停止 cat_108",
        step_mode="auto",
    )


@capability("微观表征设备")
def micro_check_status() -> DeviceCapability:
    """检查状态。"""
    return DeviceCapability(
        capability_key="micro_108.check_status",
        device_category="微观表征设备",
        name="检查状态",
        description="查询 micro_108 当前状态",
        step_mode="auto",
    )


@capability("微观表征设备")
def micro_power_on() -> DeviceCapability:
    """启动。"""
    return DeviceCapability(
        capability_key="micro_108.power_on",
        device_category="微观表征设备",
        name="启动",
        description="启动 micro_108",
        step_mode="auto",
    )


@capability("微观表征设备")
def micro_power_off() -> DeviceCapability:
    """停止。"""
    return DeviceCapability(
        capability_key="micro_108.power_off",
        device_category="微观表征设备",
        name="停止",
        description="停止 micro_108",
        step_mode="auto",
    )


def _request_station(
    device_action_key: str,
    action: str | None = None,
    timeout: float | None = None,
) -> dict[str, Any]:
    """调用 Station 远程接口。

    Args:
        device_action_key: 工位动作前缀。
        action: 动作名称，为空时查询状态。
        timeout: 请求超时时间。

    Returns:
        Station 服务响应。
    """
    settings = get_settings()
    base_url = settings.apis.station.base_url.rstrip("/")
    path = f"/{device_action_key}/status" if action is None else f"/{device_action_key}/action"
    payload = None if action is None else {"action": action}
    response = requests.request(
        method="POST",
        url=f"{base_url}{path}",
        timeout=timeout or settings.apis.station.timeout,
        json=payload,
    )
    response.raise_for_status()
    return response.json()
