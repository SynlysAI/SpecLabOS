"""IR 设备定义。"""

from app.devices.base import BaseDevice
from app.domain.device_action import ActionSpec


def _build_sim_executor(device_key: str, action_name: str):
    """构造模拟动作执行器。"""

    def _executor(params, _context):
        return {
            "device": device_key,
            "action": action_name,
            "status": "completed",
            "response": params,
        }

    return _executor


def build_ir_device(sim_mode: bool) -> BaseDevice:
    """构建 IR 设备实例。"""
    return BaseDevice(
        key="ir_2278",
        name="ir_2278",
        category="红外光谱仪",
        device_type="IRSpectrometer",
        location="A-110",
        sim_mode=sim_mode,
        actions=[
            ActionSpec(
                action_key="ir.check_status",
                name="检查状态",
                description="查询 IR 当前状态",
                executor=_build_sim_executor("ir_2278", "check_status"),
            ),
            ActionSpec(
                action_key="ir.power_on",
                name="启动",
                description="启动 IR 设备",
                executor=_build_sim_executor("ir_2278", "power_on"),
            ),
            ActionSpec(
                action_key="ir.power_off",
                name="停止",
                description="停止 IR 设备",
                executor=_build_sim_executor("ir_2278", "power_off"),
            ),
        ],
    )
