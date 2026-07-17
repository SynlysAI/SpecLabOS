"""用户设备控制权限仓储。"""

from datetime import UTC, datetime
from typing import Optional


class DevicePermissionRepository:
    """用户对设备控制权限的数据访问层。

    权限模型说明:
        - 表中存在记录即表示该用户对该设备有 control 权限。
        - 读(read)权限默认对所有登录用户开放,不入表。
        - admin 角色绕过权限检查,直接放行。
        - 撤销授权等价于删除记录。
    """

    COLLECTION_NAME = "user_device_permissions"

    def __init__(self, database) -> None:
        """初始化权限仓储。

        Args:
            database: MongoDB 数据库实例。
        """
        self._collection = database[self.COLLECTION_NAME]
        self._ensure_indexes()

    def _ensure_indexes(self) -> None:
        """创建必要索引。

        Args:
            无参数。

        Returns:
            无返回值。
        """
        try:
            self._collection.create_index(
                [("user_id", 1), ("device_key", 1)],
                unique=True,
                name="uniq_user_device",
            )
            self._collection.create_index(
                "device_key", name="idx_device_key"
            )
            self._collection.create_index(
                "user_id", name="idx_user_id"
            )
        except Exception:
            # mongomock 与真实 Mongo 行为差异时忽略(如 OperationFailure code 85)
            pass

    def list_device_keys_by_user(self, user_id: str) -> list[str]:
        """返回某用户拥有 control 权限的全部设备标识。

        Args:
            user_id: 用户唯一 ID。

        Returns:
            设备标识列表,无记录时返回空列表。
        """
        cursor = self._collection.find(
            {"user_id": user_id}, {"device_key": 1, "_id": 0}
        )
        return [doc["device_key"] for doc in cursor if doc.get("device_key")]

    def list_user_ids_by_device(self, device_key: str) -> list[str]:
        """返回某设备已授权的全部用户 ID。

        Args:
            device_key: 设备唯一标识。

        Returns:
            用户 ID 列表,无记录时返回空列表。
        """
        cursor = self._collection.find(
            {"device_key": device_key}, {"user_id": 1, "_id": 0}
        )
        return [doc["user_id"] for doc in cursor if doc.get("user_id")]

    def list_grants_by_user(self, user_id: str) -> list[dict]:
        """返回某用户的全部授权记录(含元数据)。

        Args:
            user_id: 用户唯一 ID。

        Returns:
            授权记录列表,按授权时间倒序。
        """
        return list(
            self._collection.find({"user_id": user_id}).sort("granted_at", -1)
        )

    def list_grants_by_device(self, device_key: str) -> list[dict]:
        """返回某设备的全部授权记录(含元数据)。

        Args:
            device_key: 设备唯一标识。

        Returns:
            授权记录列表,按授权时间倒序。
        """
        return list(
            self._collection.find({"device_key": device_key}).sort(
                "granted_at", -1
            )
        )

    def has_access(self, user_id: str, device_key: str) -> bool:
        """检查用户是否对设备有 control 权限。

        Args:
            user_id: 用户唯一 ID。
            device_key: 设备唯一标识。

        Returns:
            存在授权记录返回 True,否则 False。
        """
        return self._collection.find_one(
            {"user_id": user_id, "device_key": device_key}, {"_id": 1}
        ) is not None

    def find_grant(
        self, user_id: str, device_key: str
    ) -> Optional[dict]:
        """查询单条授权记录。

        Args:
            user_id: 用户唯一 ID。
            device_key: 设备唯一标识。

        Returns:
            授权记录或 None。
        """
        return self._collection.find_one(
            {"user_id": user_id, "device_key": device_key}
        )

    def grant(
        self,
        user_id: str,
        device_key: str,
        granted_by: str,
    ) -> dict:
        """授予设备控制权限(幂等)。

        若授权已存在,原样返回不更新 granted_at,避免刷新原始授权时间。

        Args:
            user_id: 被授权用户 ID。
            device_key: 设备唯一标识。
            granted_by: 授权人 user_id。

        Returns:
            当前授权记录。
        """
        existing = self._collection.find_one(
            {"user_id": user_id, "device_key": device_key}
        )
        if existing:
            return existing

        now = datetime.now(UTC)
        document = {
            "user_id": user_id,
            "device_key": device_key,
            "permission_level": "control",
            "granted_by": granted_by,
            "granted_at": now,
        }
        self._collection.insert_one(document)
        return document

    def revoke(self, user_id: str, device_key: str) -> bool:
        """撤销设备控制权限。

        Args:
            user_id: 用户唯一 ID。
            device_key: 设备唯一标识。

        Returns:
            是否删除了记录。
        """
        result = self._collection.delete_one(
            {"user_id": user_id, "device_key": device_key}
        )
        return result.deleted_count > 0

    def replace_user_devices(
        self,
        user_id: str,
        device_keys: list[str],
        granted_by: str,
    ) -> None:
        """覆盖式设置某用户的可控设备集合。

        Args:
            user_id: 被授权用户 ID。
            device_keys: 新的设备标识完整列表。
            granted_by: 授权人 user_id。

        Returns:
            无返回值。
        """
        desired = set(device_keys)
        existing = set(self.list_device_keys_by_user(user_id))

        for device_key in existing - desired:
            self.revoke(user_id, device_key)
        for device_key in desired - existing:
            self.grant(user_id, device_key, granted_by)

    def replace_device_users(
        self,
        device_key: str,
        user_ids: list[str],
        granted_by: str,
    ) -> None:
        """覆盖式设置某设备的授权用户集合。

        Args:
            device_key: 设备唯一标识。
            user_ids: 新的用户 ID 完整列表。
            granted_by: 授权人 user_id。

        Returns:
            无返回值。
        """
        desired = set(user_ids)
        existing = set(self.list_user_ids_by_device(device_key))

        for user_id in existing - desired:
            self.revoke(user_id, device_key)
        for user_id in desired - existing:
            self.grant(user_id, device_key, granted_by)
