"""日志仓储实现。"""

from datetime import datetime, timezone


class LogRepository:
    """工作流与设备日志仓储。"""

    def __init__(self, database) -> None:
        """初始化日志仓储。

        Args:
            database: MongoDB 数据库实例。
        """
        self._collection = database["logs"]

    def create(self, payload: dict) -> dict:
        """写入日志记录。

        Args:
            payload: 待持久化的日志数据。

        Returns:
            补全时间戳后的日志数据。
        """
        document = {
            "created_at": datetime.now(timezone.utc),
            **payload,
        }
        self._collection.insert_one(document)
        return document

    def list_by_run_id(self, run_id: str) -> list[dict]:
        """按工作流运行标识查询日志记录。

        Args:
            run_id: 工作流运行唯一标识。

        Returns:
            对应运行的日志记录列表。
        """
        return list(self._collection.find({"run_id": run_id}))
