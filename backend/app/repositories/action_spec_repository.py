"""动作规范仓储实现。"""


class ActionSpecRepository:
    """动作规范仓储。"""

    def __init__(self, database) -> None:
        """初始化动作规范仓储。

        Args:
            database: MongoDB 数据库实例。
        """
        self._collection = database["action_specs"]

    def get_by_key(self, action_key: str):
        """按动作标识查询动作规范。

        Args:
            action_key: 动作唯一标识。

        Returns:
            对应动作规范，不存在时返回 None。
        """
        return self._collection.find_one({"action_key": action_key})

    def upsert(self, action_key: str, payload: dict) -> None:
        """插入或更新动作规范。

        Args:
            action_key: 动作唯一标识。
            payload: 待持久化的动作规范数据。
        """
        document = {"action_key": action_key, **payload}
        self._collection.update_one(
            {"action_key": action_key},
            {"$set": document},
            upsert=True,
        )
