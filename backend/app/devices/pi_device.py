"""PI 设备定义。"""

from typing import Any

from app.devices.base import BaseDevice
from app.domain.device_action import ActionSpec


def _run_simple_action(action_name: str):
    """构造 PI 的简单模拟动作。"""

    def _executor(params: dict[str, Any], _context: dict[str, Any]) -> dict[str, Any]:
        return {
            "device": "pi_2278",
            "action": action_name,
            "status": "completed",
            "response": params,
        }

    return _executor


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
        actions=[
            ActionSpec(
                action_key="pi.health_check",
                name="健康检查",
                description="检查 PI 服务健康状态",
                executor=_run_simple_action("health_check"),
            ),
            ActionSpec(
                action_key="pi.power_on",
                name="启动",
                description="触发 PI 启动按钮",
                executor=_run_simple_action("power_on"),
            ),
            ActionSpec(
                action_key="pi.pause",
                name="暂停",
                description="触发 PI 暂停按钮",
                executor=_run_simple_action("pause"),
            ),
            ActionSpec(
                action_key="pi.power_off",
                name="停止",
                description="触发 PI 停止按钮",
                executor=_run_simple_action("power_off"),
            ),
            ActionSpec(
                action_key="pi.get_config",
                name="查询配置参数",
                description="查询 PI 配置参数",
                executor=_run_simple_action("get_config"),
            ),
            ActionSpec(
                action_key="pi.update_config",
                name="修改配置参数",
                description="修改 PI 配置参数",
                parameter_schema=[
                    {"name": "config_data", "type": "json", "required": True},
                ],
                executor=_run_simple_action("update_config"),
            ),
        ],
    )
