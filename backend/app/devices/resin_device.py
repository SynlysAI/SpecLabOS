"""树脂处理设备定义。"""

from typing import Any

from app.devices.base import BaseDevice
from app.domain.device_action import ActionSpec


def _run_simple_action(action_name: str, device_name: str):
    """构造 Resin 的简单模拟动作。"""

    def _executor(params: dict[str, Any], _context: dict[str, Any]) -> dict[str, Any]:
        return {
            "device": device_name,
            "action": action_name,
            "status": "completed",
            "response": params,
        }

    return _executor


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
        actions=[
            ActionSpec(
                action_key="resin.health_check",
                name="健康检查",
                description="检查 Resin 工作站健康状态",
                executor=_run_simple_action("health_check", key),
            ),
            ActionSpec(
                action_key="resin.trigger_generate",
                name="触发解析",
                description="触发 Resin 解析实验方案",
                parameter_schema=[
                    {"name": "experiment_plan", "type": "string", "required": True},
                ],
                executor=_run_simple_action("trigger_generate", key),
            ),
            ActionSpec(
                action_key="resin.execute_process",
                name="执行流程",
                description="执行 Resin 工作流程",
                executor=_run_simple_action("execute_process", key),
            ),
            ActionSpec(
                action_key="resin.check_execution_status",
                name="查询流程状态",
                description="查询 Resin 流程执行状态",
                executor=_run_simple_action("check_execution_status", key),
            ),
            ActionSpec(
                action_key="resin.wait_execution_completed",
                name="等待执行完成",
                description="轮询 Resin 流程直到完成",
                parameter_schema=[
                    {"name": "poll_interval_seconds", "type": "number", "required": False},
                    {"name": "timeout_seconds", "type": "number", "required": False},
                ],
                executor=_run_simple_action("wait_execution_completed", key),
            ),
        ],
    )
