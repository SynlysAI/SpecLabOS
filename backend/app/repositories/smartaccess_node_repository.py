"""SmartAccess 执行端节点心跳仓储。"""

from datetime import datetime, timezone
from typing import Any, Optional


class SmartAccessNodeRepository:
    """SmartAccess 节点在线状态仓储。

    集合名: ``smartaccess_nodes``。每条记录对应一个 SmartAccess 执行端,
    通过周期心跳维护在线状态,供设备监控页与远程运行入口判定可达性。
    """

    def __init__(self, database) -> None:
        """初始化节点仓储。

        Args:
            database: MongoDB 数据库实例。
        """
        self._collection = database["smartaccess_nodes"]
        try:
            self._collection.create_index("node_id", unique=True)
        except Exception:  # noqa: BLE001 - 索引已存在或 Mongo 不可用时忽略
            pass

    def upsert_heartbeat(
        self,
        node_id: str,
        *,
        device_info: Optional[dict[str, Any]] = None,
        heartbeat_interval_seconds: Optional[int] = None,
    ) -> dict:
        """写入或刷新节点心跳。

        首次上报时插入文档并记录 ``first_seen_at``;后续上报仅刷新
        ``last_heartbeat_at``、``status`` 与可选的设备元信息。

        Args:
            node_id: SmartAccess 执行端标识。
            device_info: 执行端上报的设备元信息。
            heartbeat_interval_seconds: 执行端上报周期,用于精确判离线。

        Returns:
            更新后的节点文档。
        """
        now = datetime.now(timezone.utc)
        set_on_insert = {
            "node_id": node_id,
            "first_seen_at": now,
        }
        set_fields: dict[str, Any] = {
            "last_heartbeat_at": now,
            "status": "online",
            "updated_at": now,
        }
        if device_info is not None:
            set_fields["device_info"] = device_info
        if heartbeat_interval_seconds is not None:
            set_fields["heartbeat_interval_seconds"] = int(heartbeat_interval_seconds)

        update: dict[str, Any] = {"$set": set_fields, "$setOnInsert": set_on_insert}
        result = self._collection.find_one_and_update(
            {"node_id": node_id},
            update,
            upsert=True,
            return_document=True,
        )
        return result or {
            **set_on_insert,
            **set_fields,
        }

    def mark_offline(self, node_id: str) -> None:
        """将指定节点标记为离线。

        Args:
            node_id: SmartAccess 执行端标识。
        """
        self._collection.update_one(
            {"node_id": node_id, "status": {"$ne": "offline"}},
            {
                "$set": {
                    "status": "offline",
                    "updated_at": datetime.now(timezone.utc),
                }
            },
        )

    def list_nodes(self) -> list[dict]:
        """返回全部节点记录。

        Returns:
            节点文档列表,按 ``last_heartbeat_at`` 降序。
        """
        return list(
            self._collection.find({}).sort(
                "last_heartbeat_at", -1
            )
        )

    def find_node(self, node_id: str) -> Optional[dict]:
        """按节点 ID 查询。

        Args:
            node_id: SmartAccess 执行端标识。

        Returns:
            节点文档或 None。
        """
        return self._collection.find_one({"node_id": node_id})

    def list_stale_nodes(self, threshold_seconds: int) -> list[dict]:
        """返回超过阈值未心跳的在线节点。

        Args:
            threshold_seconds: 判定离线的超时秒数。

        Returns:
            待标记离线的节点文档列表。
        """
        from datetime import timedelta

        cutoff = datetime.now(timezone.utc) - timedelta(seconds=threshold_seconds)
        return list(
            self._collection.find(
                {
                    "status": "online",
                    "last_heartbeat_at": {"$lt": cutoff},
                }
            )
        )
