"""外部实验任务 MongoDB 仓储。"""


class ExternalExperimentDispatchRepository:
    """管理外部实验任务批次记录。"""

    def __init__(self, database) -> None:
        """初始化仓储。

        Args:
            database: MongoDB 数据库实例。
        """
        self._collection = database["external_experiment_dispatches"]

    def create(self, record: dict) -> dict:
        """创建一条外部实验任务批次记录。

        Args:
            record: 待持久化的任务记录。

        Returns:
            已保存的任务记录。
        """
        self._collection.insert_one(record)
        return dict(record)

    def list(self, keyword: str | None = None) -> list[dict]:
        """查询外部实验任务批次列表。

        Args:
            keyword: 按任务、对象或来源筛选的关键词。

        Returns:
            按接收时间倒序排列的任务记录。
        """
        query = {}
        if keyword:
            query["$or"] = [
                {"experiment_name": {"$regex": keyword, "$options": "i"}},
                {
                    "experiment_object.name": {
                        "$regex": keyword,
                        "$options": "i",
                    }
                },
                {"source_system": {"$regex": keyword, "$options": "i"}},
                {"source_module": {"$regex": keyword, "$options": "i"}},
            ]
        return list(self._collection.find(query, {"_id": 0}).sort("received_at", -1))

    def get(self, dispatch_id: str) -> dict | None:
        """查询指定外部实验任务批次。

        Args:
            dispatch_id: 外部实验任务批次标识。

        Returns:
            任务记录；不存在时返回 None。
        """
        return self._collection.find_one({"dispatch_id": dispatch_id}, {"_id": 0})
