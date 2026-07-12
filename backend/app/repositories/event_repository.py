"""运行事件仓储。"""

from app.core.data_db import get_data_database
from app.domain.run_event import RunEvent


class EventRepository:
    """运行事件仓储，借鉴 Dagster EventLogStorage。

    事件是不可变的追加日志。
    """

    COLLECTION = "run_events"

    def __init__(self):
        """初始化事件仓储，确保索引存在。"""
        self._collection = get_data_database()[self.COLLECTION]
        self._collection.create_index([("run_id", 1), ("timestamp", 1)])
        self._collection.create_index([("device_id", 1), ("timestamp", -1)])

    def store_event(self, event: RunEvent) -> None:
        """追加事件。

        Args:
            event: 运行事件。
        """
        doc = event.model_dump()
        doc["_id"] = doc.pop("event_id")
        self._collection.insert_one(doc)

    def get_events(self, run_id: str) -> list[RunEvent]:
        """获取运行的完整事件链。

        Args:
            run_id: 运行标识。

        Returns:
            按时间排序的事件列表。
        """
        cursor = self._collection.find({"run_id": run_id}).sort("timestamp", 1)
        return [self._doc_to_event(doc) for doc in cursor]

    def get_latest_event(self, run_id: str) -> RunEvent | None:
        """获取最新事件。

        Args:
            run_id: 运行标识。

        Returns:
            最新事件，无事件时返回 None。
        """
        doc = self._collection.find_one(
            {"run_id": run_id}, sort=[("timestamp", -1)]
        )
        return self._doc_to_event(doc) if doc else None

    def get_events_by_device(self, device_id: str, limit: int = 50) -> list[RunEvent]:
        """获取设备相关的最近事件。

        Args:
            device_id: 设备标识。
            limit: 最大返回数量。

        Returns:
            事件列表。
        """
        cursor = self._collection.find(
            {"device_id": device_id}
        ).sort("timestamp", -1).limit(limit)
        return [self._doc_to_event(doc) for doc in cursor]

    @staticmethod
    def _doc_to_event(doc: dict) -> RunEvent:
        """将 MongoDB 文档转换为 RunEvent。

        Args:
            doc: MongoDB 文档。

        Returns:
            RunEvent 实例。
        """
        doc["event_id"] = doc.pop("_id")
        return RunEvent(**doc)
