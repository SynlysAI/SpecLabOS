"""SmartAccess 已同步设备仓储。"""

from datetime import datetime, timezone


def _now_text() -> str:
    """返回当前 UTC 时间文本。"""
    return datetime.now(timezone.utc).isoformat()


class SmartAccessDeviceRepository:
    """保存设备接入页同步上来的仪器档案。"""

    def __init__(self, database) -> None:
        """初始化仓储。

        Args:
            database: MongoDB 数据库实例。
        """
        self._devices = database["smartaccess_devices"]
        try:
            self._devices.create_index("device_id", unique=True)
        except Exception:  # noqa: BLE001 - 索引已存在或 Mongo 不可用时忽略
            pass

    def upsert_device(
        self,
        device_id: str,
        node_id: str,
        *,
        name: str = "",
        window_title: str = "",
    ) -> dict:
        """保存或更新一台已同步设备。

        Args:
            device_id: 仪器设备 ID。
            node_id: 所属执行端 ID。
            name: 展示名称。
            window_title: 绑定的窗口标题。

        Returns:
            设备记录。
        """
        record = {
            "device_id": device_id,
            "node_id": node_id,
            "name": name or device_id,
            "window_title": window_title,
            "updated_at": _now_text(),
        }
        self._devices.update_one({"device_id": device_id}, {"$set": record}, upsert=True)
        return record

    def list_devices(self) -> list[dict]:
        """列出已同步设备。"""
        return list(self._devices.find({}))

    def delete_device(self, device_id: str) -> bool:
        """删除已同步的仪器档案。

        Args:
            device_id: 仪器设备 ID。

        Returns:
            是否删除到记录。
        """
        result = self._devices.delete_one({"device_id": device_id})
        return result.deleted_count > 0
