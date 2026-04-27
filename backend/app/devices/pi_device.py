"""PI 设备定义。"""

from app.devices.base import BaseDevice


def build_pi_device(sim_mode: bool) -> BaseDevice:
    """构建 PI 设备实例。

    Args:
        sim_mode: 是否启用模拟模式。

    Returns:
        预留后续扩展的 PI 设备实例。
    """
    return BaseDevice(
        key="pi_2278",
        name="pi_2278",
        category="PI 合成系统",
        device_type="PISynthesisSystem",
        location="A-301",
        sim_mode=sim_mode,
    )
