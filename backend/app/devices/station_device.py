"""工位设备定义。"""

from typing import Any

from app.devices.base import BaseDevice
from app.domain.device_action import ActionSpec


def _run_simple_action(action_name: str, device_name: str):
    """构造工位设备的简单模拟动作。"""

    def _executor(params: dict[str, Any], _context: dict[str, Any]) -> dict[str, Any]:
        return {
            "device": device_name,
            "action": action_name,
            "status": "completed",
            "response": params,
        }

    return _executor


def build_station_device(
    sim_mode: bool,
    key: str = "station_001",
    device_type: str = "MicroCharacterizationDevice",
    category: str = "工位设备",
    location: str = "C-101",
) -> BaseDevice:
    """构建设备工位实例。

    Args:
        sim_mode: 是否启用模拟模式。
        key: 设备实例标识。
        device_type: 设备类型标识。
        category: 设备展示分类。
        location: 设备所在位置。

    Returns:
        预留后续扩展的工位设备实例。
    """
    return BaseDevice(
        key=key,
        name=key,
        category=category,
        device_type=device_type,
        location=location,
        sim_mode=sim_mode,
        actions=[
            ActionSpec(
                action_key=f"{key}.check_status",
                name="检查状态",
                description=f"查询 {key} 当前状态",
                executor=_run_simple_action("check_status", key),
            ),
            ActionSpec(
                action_key=f"{key}.power_on",
                name="启动",
                description=f"启动 {key}",
                executor=_run_simple_action("power_on", key),
            ),
            ActionSpec(
                action_key=f"{key}.power_off",
                name="停止",
                description=f"停止 {key}",
                executor=_run_simple_action("power_off", key),
            ),
            ActionSpec(
                action_key=f"{key}.wait_completed",
                name="等待执行完成",
                description=f"等待 {key} 执行完成",
                parameter_schema=[
                    {"name": "poll_interval_seconds", "type": "number", "required": False},
                    {"name": "timeout_seconds", "type": "number", "required": False},
                ],
                executor=_run_simple_action("wait_completed", key),
            ),
        ],
    )
