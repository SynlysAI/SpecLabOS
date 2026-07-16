"""设备集成能力模板。"""

from typing import Any

from app.devices.registry import capability, local_executor
from app.domain.capability import DeviceCapability


@local_executor("example_001", "example.check_status")
def example_check_status_executor(
    params: dict[str, Any],
    context: dict[str, Any],
) -> dict[str, Any]:
    """查询示例设备状态。

    Args:
        params: 执行参数。
        context: 运行上下文。

    Returns:
        示例设备状态。
    """
    return {"status": "idle", "params": params}


@capability("示例设备")
def example_check_status() -> DeviceCapability:
    """检查状态。"""
    return DeviceCapability(
        capability_key="example.check_status",
        device_category="示例设备",
        name="检查状态",
        description="查询示例设备当前状态",
        step_mode="auto",
    )
