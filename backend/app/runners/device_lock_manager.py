"""设备锁管理器。"""

from threading import Lock


class DeviceLockManager:
    """管理按设备粒度的运行互斥锁。"""

    def __init__(self) -> None:
        """初始化设备锁管理器。"""
        self._guard = Lock()
        self._holders: dict[str, dict[str, int | str]] = {}

    def acquire(self, device_key: str, run_id: str) -> bool:
        """尝试获取指定设备的占用权。

        Args:
            device_key: 设备唯一标识。
            run_id: 当前工作流运行标识。

        Returns:
            若成功获取或当前运行已持有该设备，则返回 True。
        """
        with self._guard:
            holder = self._holders.get(device_key)
            if holder is None:
                self._holders[device_key] = {"run_id": run_id, "count": 1}
                return True
            if holder["run_id"] == run_id:
                holder["count"] = int(holder["count"]) + 1
                return True
            return False

    def release(self, device_key: str, run_id: str) -> None:
        """释放指定设备的占用权。

        Args:
            device_key: 设备唯一标识。
            run_id: 当前工作流运行标识。
        """
        with self._guard:
            holder = self._holders.get(device_key)
            if holder is None or holder["run_id"] != run_id:
                return
            holder["count"] = int(holder["count"]) - 1
            if int(holder["count"]) <= 0:
                self._holders.pop(device_key, None)
