"""LCMS 设备定义。"""

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


def build_lcms_device(sim_mode: bool) -> BaseDevice:
    """构建 LCMS 设备实例。"""
    return BaseDevice(
        key="lcms_2278",
        name="lcms_2278",
        category="液相色谱质谱联用仪",
        device_type="LCMSAnalyzer",
        location="A-126",
        sim_mode=sim_mode,
        actions=[
            ActionSpec(
                action_key="lcms.check_status",
                name="检查状态",
                description="查询 LCMS 当前状态",
                executor=_build_sim_executor("lcms_2278", "check_status"),
            ),
            ActionSpec(
                action_key="lcms.power_on",
                name="启动",
                description="启动 LCMS 设备",
                executor=_build_sim_executor("lcms_2278", "power_on"),
            ),
            ActionSpec(
                action_key="lcms.power_off",
                name="停止",
                description="停止 LCMS 设备",
                executor=_build_sim_executor("lcms_2278", "power_off"),
            ),
        ],
    )
