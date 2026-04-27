"""GPC 设备定义。"""

from app.devices.base import BaseDevice


def build_gpc_device(sim_mode: bool) -> BaseDevice:
    """构建 GPC 设备实例。

    Args:
        sim_mode: 是否启用模拟模式。

    Returns:
        预留后续扩展的 GPC 设备实例。
    """
    return BaseDevice(
        key="gpc_2278",
        name="gpc_2278",
        category="凝胶渗透色谱仪",
        device_type="GPCAnalyzer",
        location="A-105",
        sim_mode=sim_mode,
    )
