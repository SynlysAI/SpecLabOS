"""IR 设备定义。"""

from typing import Any

from app.devices.registry import capability, device, local_executor
from app.domain.capability import DeviceCapability
from app.domain.device import DeviceResource


@device
class IRDevice(DeviceResource):
    """IR 红外光谱仪。"""

    device_id: str = "ir_2278"
    name: str = "ir_2278"
    category: str = "红外光谱仪"
    device_type: str = "IRSpectrometer"
    location: str = "A-110"


@local_executor("ir_2278", "ir.check_status")
def ir_check_status_executor(
    params: dict[str, Any],
    context: dict[str, Any],
) -> dict[str, Any]:
    """执行 IR 状态检查。

    Args:
        params: 执行参数。
        context: 运行上下文。

    Returns:
        模拟执行结果。
    """
    return _build_sim_result("ir_2278", "check_status", params)


@local_executor("ir_2278", "ir.power_on")
def ir_power_on_executor(
    params: dict[str, Any],
    context: dict[str, Any],
) -> dict[str, Any]:
    """执行 IR 启动。

    Args:
        params: 执行参数。
        context: 运行上下文。

    Returns:
        模拟执行结果。
    """
    return _build_sim_result("ir_2278", "power_on", params)


@local_executor("ir_2278", "ir.power_off")
def ir_power_off_executor(
    params: dict[str, Any],
    context: dict[str, Any],
) -> dict[str, Any]:
    """执行 IR 停止。

    Args:
        params: 执行参数。
        context: 运行上下文。

    Returns:
        模拟执行结果。
    """
    return _build_sim_result("ir_2278", "power_off", params)


@capability("红外光谱仪")
def ir_check_status() -> DeviceCapability:
    """检查状态。"""
    return DeviceCapability(
        capability_key="ir.check_status",
        device_category="红外光谱仪",
        name="检查状态",
        description="查询 IR 当前状态",
        step_mode="auto",
    )


@capability("红外光谱仪")
def ir_power_on() -> DeviceCapability:
    """启动。"""
    return DeviceCapability(
        capability_key="ir.power_on",
        device_category="红外光谱仪",
        name="启动",
        description="启动 IR 设备",
        step_mode="auto",
    )


@capability("红外光谱仪")
def ir_power_off() -> DeviceCapability:
    """停止。"""
    return DeviceCapability(
        capability_key="ir.power_off",
        device_category="红外光谱仪",
        name="停止",
        description="停止 IR 设备",
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
