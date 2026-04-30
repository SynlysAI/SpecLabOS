"""设备服务。"""

from datetime import datetime

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

    def list_devices(self):
        """列出所有已注册设备实例。"""
        return self._registry.list_devices()

    @staticmethod
    def serialize_device(device) -> dict:
        """将设备实例转换为前端可直接消费的字典。"""
        status = device.get_status()
        updated_at = status.updated_at or datetime.now().strftime("%Y-%m-%d %H:%M")
        return {
            "key": device.key,
            "name": device.name,
            "category": device.category,
            "device_type": device.device_type or device.category,
            "enabled": device.enabled,
            "sim_mode": device.sim_mode,
            "location": device.location,
            "connection": device.connection,
            "status_snapshot": {
                "state": status.state,
                "message": status.message,
                "updated_at": updated_at,
            },
        }
