"""设备构建工厂。"""

from collections.abc import Callable
from functools import lru_cache
from typing import Any

from app.devices.base import BaseDevice
from app.devices.gpc_device import build_gpc_device
from app.devices.nmr_device import build_nmr_device
from app.devices.pi_device import build_pi_device
from app.devices.resin_device import build_resin_device
from app.devices.station_device import build_station_device


def _build_simple_device(
    key: str,
    category: str,
    device_type: str,
    location: str,
    sim_mode: bool,
    actions: list[dict[str, Any]],
) -> BaseDevice:
    """构造带动作目录的简单设备实例。"""
    from app.domain.device_action import ActionSpec

    def _build_executor(action_name: str):
        def _executor(params: dict[str, Any], _context: dict[str, Any]) -> dict[str, Any]:
            return {
                "device": key,
                "action": action_name,
                "status": "completed",
                "response": params,
            }

        return _executor

    return BaseDevice(
        key=key,
        name=key,
        category=category,
        device_type=device_type,
        location=location,
        sim_mode=sim_mode,
        actions=[
            ActionSpec(
                action_key=action["action_key"],
                name=action["name"],
                description=action["description"],
                parameter_schema=action.get("parameter_schema", []),
                executor=_build_executor(action["action_key"]),
            )
            for action in actions
        ],
    )


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
        _build_simple_device(
            key="ir_2278",
            category="红外光谱仪",
            device_type="IRSpectrometer",
            location="A-110",
            sim_mode=sim_mode,
            actions=[
                {
                    "action_key": "ir.check_status",
                    "name": "检查状态",
                    "description": "查询 IR 设备状态",
                },
                {
                    "action_key": "ir.power_on",
                    "name": "启动",
                    "description": "启动 IR 设备",
                },
                {
                    "action_key": "ir.power_off",
                    "name": "停止",
                    "description": "停止 IR 设备",
                },
            ],
        ),
        _build_simple_device(
            key="raman_2278",
            category="拉曼光谱仪",
            device_type="RamanSpectrometer",
            location="A-118",
            sim_mode=sim_mode,
            actions=[
                {
                    "action_key": "raman.check_status",
                    "name": "检查状态",
                    "description": "查询 Raman 状态",
                },
                {
                    "action_key": "raman.power_on",
                    "name": "启动",
                    "description": "启动 Raman 设备",
                },
                {
                    "action_key": "raman.power_off",
                    "name": "停止",
                    "description": "停止 Raman 设备",
                },
                {
                    "action_key": "raman.capture_task",
                    "name": "下发采集任务",
                    "description": "向 Raman 下发采集任务",
                    "parameter_schema": [
                        {"name": "req_id", "type": "string", "required": True},
                        {"name": "capture", "type": "json", "required": True},
                    ],
                },
                {
                    "action_key": "raman.check_result",
                    "name": "查询任务状态",
                    "description": "查询 Raman 任务结果",
                    "parameter_schema": [
                        {"name": "req_id", "type": "string", "required": True},
                    ],
                },
            ],
        ),
        _build_simple_device(
            key="lcms_2278",
            category="液相色谱质谱联用仪",
            device_type="LCMSAnalyzer",
            location="A-126",
            sim_mode=sim_mode,
            actions=[
                {
                    "action_key": "lcms.check_status",
                    "name": "检查状态",
                    "description": "查询 LCMS 状态",
                },
                {
                    "action_key": "lcms.power_on",
                    "name": "启动",
                    "description": "启动 LCMS 设备",
                },
                {
                    "action_key": "lcms.power_off",
                    "name": "停止",
                    "description": "停止 LCMS 设备",
                },
            ],
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
