"""NMR 设备定义。"""

from typing import Any

from app.devices.base import BaseDevice
from app.domain.device_action import ActionSpec


def _check_status(_params: dict[str, Any], _context: dict[str, Any]) -> dict[str, Any]:
    """模拟查询 NMR 设备状态。"""
    return {"status": "idle"}


def _start_task(params: dict[str, Any], _context: dict[str, Any]) -> dict[str, Any]:
    """模拟提交 NMR 任务。

    Args:
        params: 动作执行参数。
        _context: 动作执行上下文。

    Returns:
        提交后的任务结果。
    """
    return {
        "status": "submitted",
        "task_code": params.get("task_code", "demo-task"),
    }


def build_nmr_device(sim_mode: bool) -> BaseDevice:
    """构建 NMR 设备实例。

    Args:
        sim_mode: 是否启用模拟模式。

    Returns:
        可注册的 NMR 设备实例。
    """
    return BaseDevice(
        key="nmr_2278",
        name="NMR 2278",
        category="nmr",
        sim_mode=sim_mode,
        actions=[
            ActionSpec(
                action_key="nmr.check_status",
                name="检查状态",
                description="查询 NMR 当前状态",
                executor=_check_status,
            ),
            ActionSpec(
                action_key="nmr.start_task",
                name="启动任务",
                description="提交 NMR 检测任务",
                parameter_schema=[
                    {
                        "name": "task_code",
                        "type": "string",
                        "required": True,
                    }
                ],
                executor=_start_task,
            ),
        ],
    )
