"""设备状态轮询器。"""

from app.services.device_service import DeviceService


class StatusPoller:
    """按设备轮询状态的最小骨架实现。"""

    def __init__(self, device_service: DeviceService) -> None:
        """初始化状态轮询器。

        Args:
            device_service: 提供设备查询能力的服务。
        """
        self._device_service = device_service

    def poll(self, device_key: str) -> dict:
        """轮询指定设备状态。

        Args:
            device_key: 设备唯一标识。

        Returns:
            标准化后的设备状态字典。
        """
        status = self._device_service.get_status(device_key)
        return {
            "device_key": device_key,
            "state": status.state,
            "message": status.message,
            "updated_at": status.updated_at,
        }
