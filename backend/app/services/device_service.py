"""设备服务。"""

from app.devices.registry import DeviceRegistry
from app.devices.base import DeviceStatus


class DeviceService:
    """封装设备查询与状态读取能力。"""

    def __init__(self, registry: DeviceRegistry) -> None:
        """初始化设备服务。

        Args:
            registry: 设备注册表。
        """
        self._registry = registry

    def get_device(self, device_key: str):
        """获取指定设备实例。

        Args:
            device_key: 设备唯一标识。

        Returns:
            已注册的设备实例。
        """
        return self._registry.get_device(device_key)

    def get_status(self, device_key: str) -> DeviceStatus:
        """读取指定设备状态。

        Args:
            device_key: 设备唯一标识。

        Returns:
            当前设备状态。
        """
        return self.get_device(device_key).get_status()
