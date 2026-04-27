"""树脂处理设备定义。"""

from app.devices.base import BaseDevice


def build_resin_device(
    sim_mode: bool,
    key: str = "resin_2278",
    location: str = "B-201",
) -> BaseDevice:
    """构建树脂处理设备实例。

    Args:
        sim_mode: 是否启用模拟模式。
        key: 设备实例标识。
        location: 设备所在位置。

    Returns:
        预留后续扩展的树脂处理设备实例。
    """
    return BaseDevice(
        key=key,
        name=key,
        category="树脂工作站",
        device_type="ResinWorkstation",
        location=location,
        sim_mode=sim_mode,
    )
