"""设备注册表。"""

from app.devices.base import BaseDevice
from app.domain.device_action import ActionSpec


class DeviceRegistry:
    """维护设备实例注册关系。"""

    def __init__(self):
        """初始化空设备注册表。"""
        self._devices: dict[str, BaseDevice] = {}

    def register(self, device: BaseDevice) -> None:
        """注册设备实例。

        Args:
            device: 待注册的设备实例。
        """
        if device.key in self._devices:
            raise ValueError(f"设备已注册，不能重复注册: {device.key}")
        self._devices[device.key] = device

    def get_device(self, device_key: str) -> BaseDevice:
        """获取指定设备。

        Args:
            device_key: 设备唯一标识。

        Returns:
            已注册的设备实例。
        """
        return self._devices[device_key]

    def list_devices(self) -> list[BaseDevice]:
        """列出所有已注册设备。"""
        return list(self._devices.values())

    def list_actions(self, device_key: str) -> list[ActionSpec]:
        """列出指定设备支持的动作。

        Args:
            device_key: 设备唯一标识。

        Returns:
            设备动作声明列表。
        """
        return self.get_device(device_key).list_actions()
