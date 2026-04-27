"""设备构建工厂。"""

from collections.abc import Callable
from functools import lru_cache

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


@lru_cache(maxsize=1)
def build_default_devices(sim_mode: bool = True) -> tuple[BaseDevice, ...]:
    """构建与 spectrum_alab 对齐的默认设备实例集合。"""
    return (
        build_nmr_device(sim_mode),
        build_pi_device(sim_mode),
        build_gpc_device(sim_mode),
        BaseDevice(
            key="ir_2278",
            name="ir_2278",
            category="红外光谱仪",
            device_type="IRSpectrometer",
            location="A-110",
            sim_mode=sim_mode,
        ),
        BaseDevice(
            key="raman_2278",
            name="raman_2278",
            category="拉曼光谱仪",
            device_type="RamanSpectrometer",
            location="A-118",
            sim_mode=sim_mode,
        ),
        BaseDevice(
            key="lcms_2278",
            name="lcms_2278",
            category="液相色谱质谱联用仪",
            device_type="LCMSAnalyzer",
            location="A-126",
            sim_mode=sim_mode,
        ),
        build_resin_device(sim_mode, key="resin_2278", location="B-201"),
        build_resin_device(sim_mode, key="resin_2278_2", location="B-202"),
        build_resin_device(sim_mode, key="resin_1438", location="B-203"),
        build_station_device(
            sim_mode,
            key="metal_108",
            device_type="MetalCoatingDevice",
            category="金属镀膜设备",
            location="C-108",
        ),
        build_station_device(
            sim_mode,
            key="cat_108",
            device_type="AdhesionTestingDevice",
            category="附着力测试设备",
            location="C-109",
        ),
        build_station_device(
            sim_mode,
            key="micro_108",
            device_type="MicroCharacterizationDevice",
            category="微观表征设备",
            location="C-110",
        ),
    )
