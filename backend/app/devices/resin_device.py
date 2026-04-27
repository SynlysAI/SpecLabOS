"""树脂处理设备定义。"""

from app.devices.base import BaseDevice


def build_resin_device(sim_mode: bool) -> BaseDevice:
    """构建树脂处理设备实例。

    Args:
        sim_mode: 是否启用模拟模式。

    Returns:
        预留后续扩展的树脂处理设备实例。
    """
    return BaseDevice(
        key="resin_001",
        name="Resin Station 001",
        category="resin",
        sim_mode=sim_mode,
    )
