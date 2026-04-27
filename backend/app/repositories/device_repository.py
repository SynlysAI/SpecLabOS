"""设备仓储实现。"""


class DeviceRepository:
    """设备定义仓储。"""

    def __init__(self, database) -> None:
        """初始化设备仓储。

        Args:
            database: MongoDB 数据库实例。
        """
        self._collection = database["devices"]

    def get_by_key(self, device_key: str):
        """按设备标识查询设备记录。

        Args:
            device_key: 设备唯一标识。

        Returns:
            对应设备记录，不存在时返回 None。
        """
        return self._collection.find_one({"device_key": device_key})

    def upsert(self, device_key: str, payload: dict) -> None:
        """插入或更新设备记录。

        Args:
            device_key: 设备唯一标识。
            payload: 待持久化的设备数据。
        """
        document = {"device_key": device_key, **payload}
        self._collection.update_one(
            {"device_key": device_key},
            {"$set": document},
            upsert=True,
        )
