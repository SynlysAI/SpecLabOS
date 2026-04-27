"""工位设备定义。"""

from app.devices.base import BaseDevice


def build_station_device(sim_mode: bool) -> BaseDevice:
    """构建设备工位实例。

    Args:
        sim_mode: 是否启用模拟模式。

    Returns:
        预留后续扩展的工位设备实例。
    """
    return BaseDevice(
        key="station_001",
        name="Station 001",
        category="station",
        sim_mode=sim_mode,
    )
