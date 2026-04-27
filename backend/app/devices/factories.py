"""设备构建工厂。"""

from collections.abc import Callable

from app.devices.base import BaseDevice
from app.devices.gpc_device import build_gpc_device
from app.devices.nmr_device import build_nmr_device
from app.devices.pi_device import build_pi_device
from app.devices.resin_device import build_resin_device
from app.devices.station_device import build_station_device


DEVICE_BUILDERS: dict[str, Callable[[bool], BaseDevice]] = {
    "nmr": build_nmr_device,
    "gpc": build_gpc_device,
    "resin": build_resin_device,
    "pi": build_pi_device,
    "station": build_station_device,
}


def build_device(category: str, sim_mode: bool = True) -> BaseDevice:
    """按设备类别构建设备实例。

    Args:
        category: 设备类别标识。
        sim_mode: 是否启用模拟模式。

    Returns:
        对应类别的设备实例。
    """
    return DEVICE_BUILDERS[category](sim_mode)


def list_supported_categories() -> list[str]:
    """列出当前支持的设备类别。"""
    return list(DEVICE_BUILDERS.keys())
