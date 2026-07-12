"""LCMS 设备定义。"""

from typing import Any

from app.devices.registry import capability, device, local_executor
from app.domain.capability import DeviceCapability
from app.domain.device import DeviceResource


@device
class LCMSDevice(DeviceResource):
    """LCMS 液相色谱质谱联用仪。"""

    device_id: str = "lcms_2278"
    name: str = "lcms_2278"
    category: str = "液相色谱质谱联用仪"
    device_type: str = "LCMSAnalyzer"
    location: str = "A-126"


@local_executor("lcms_2278", "lcms.check_status")
def lcms_check_status_executor(
    params: dict[str, Any],
    context: dict[str, Any],
) -> dict[str, Any]:
    """执行 LCMS 状态检查。

    Args:
        params: 执行参数。
        context: 运行上下文。

    Returns:
        模拟执行结果。
    """
    return _build_sim_result("lcms_2278", "check_status", params)


@local_executor("lcms_2278", "lcms.power_on")
def lcms_power_on_executor(
    params: dict[str, Any],
    context: dict[str, Any],
) -> dict[str, Any]:
    """执行 LCMS 启动。

    Args:
        params: 执行参数。
        context: 运行上下文。

    Returns:
        模拟执行结果。
    """
    return _build_sim_result("lcms_2278", "power_on", params)


@local_executor("lcms_2278", "lcms.power_off")
def lcms_power_off_executor(
    params: dict[str, Any],
    context: dict[str, Any],
) -> dict[str, Any]:
    """执行 LCMS 停止。

    Args:
        params: 执行参数。
        context: 运行上下文。

    Returns:
        模拟执行结果。
    """
    return _build_sim_result("lcms_2278", "power_off", params)


@capability("液相色谱质谱联用仪")
def lcms_check_status() -> DeviceCapability:
    """检查状态。"""
    return DeviceCapability(
        capability_key="lcms.check_status",
        device_category="液相色谱质谱联用仪",
        name="检查状态",
        description="查询 LCMS 当前状态",
        step_mode="auto",
    )


@capability("液相色谱质谱联用仪")
def lcms_power_on() -> DeviceCapability:
    """启动。"""
    return DeviceCapability(
        capability_key="lcms.power_on",
        device_category="液相色谱质谱联用仪",
        name="启动",
        description="启动 LCMS 设备",
        step_mode="auto",
    )


@capability("液相色谱质谱联用仪")
def lcms_power_off() -> DeviceCapability:
    """停止。"""
    return DeviceCapability(
        capability_key="lcms.power_off",
        device_category="液相色谱质谱联用仪",
        name="停止",
        description="停止 LCMS 设备",
        step_mode="auto",
    )


def _build_sim_result(
    device_id: str,
    action_name: str,
    params: dict[str, Any],
) -> dict[str, Any]:
    """构造模拟执行结果。

    Args:
        device_id: 设备标识。
        action_name: 动作名称。
        params: 执行参数。

    Returns:
        模拟执行结果。
    """
    return {
        "device": device_id,
        "action": action_name,
        "status": "completed",
        "response": params,
    }
