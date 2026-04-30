"""设备基类定义。"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from app.domain.device_action import ActionSpec


@dataclass
class DeviceStatus:
    """设备状态数据。"""

    state: str
    message: str = ""
    updated_at: str | None = None


@dataclass
class BaseDevice:
    """设备基础模型。"""

    key: str
    name: str
    category: str
    device_type: str = ""
    location: str = ""
    enabled: bool = True
    sim_mode: bool = True
    connection: dict[str, Any] = field(default_factory=dict)
    actions: list[ActionSpec] = field(default_factory=list)

    def get_status(self) -> DeviceStatus:
        """返回设备当前状态。"""
        return DeviceStatus(
            state="idle",
            message="simulated" if self.sim_mode else "configured",
            updated_at=datetime.now().strftime("%Y-%m-%d %H:%M"),
        )

    def list_actions(self) -> list[ActionSpec]:
        """列出设备支持的动作声明。"""
        return self.actions

    def execute_action(
        self,
        action_key: str,
        params: dict[str, Any],
        context: dict[str, Any],
    ) -> dict[str, Any]:
        """执行指定动作。

        Args:
            action_key: 设备动作唯一标识。
            params: 动作执行参数。
            context: 动作执行上下文。

        Returns:
            动作执行结果。
        """
        action_map = {action.action_key: action for action in self.actions}
        return action_map[action_key].executor(params, context)
