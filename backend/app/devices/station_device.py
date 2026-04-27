"""工位设备定义。"""

from app.devices.base import BaseDevice


def build_station_device(
    sim_mode: bool,
    key: str = "station_001",
    device_type: str = "MicroCharacterizationDevice",
    category: str = "工位设备",
    location: str = "C-101",
) -> BaseDevice:
    """构建设备工位实例。

    Args:
        sim_mode: 是否启用模拟模式。
        key: 设备实例标识。
        device_type: 设备类型标识。
        category: 设备展示分类。
        location: 设备所在位置。

    Returns:
        预留后续扩展的工位设备实例。
    """
    return BaseDevice(
        key=key,
        name=key,
        category=category,
        device_type=device_type,
        location=location,
        sim_mode=sim_mode,
    )
