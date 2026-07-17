"""设备权限判定与配置服务。"""

from typing import Iterable

from fastapi import HTTPException, status

from app.repositories.device_permission_repository import (
    DevicePermissionRepository,
)


_ANONYMOUS_USER_ID = ""


class DevicePermissionService:
    """封装权限判定逻辑,供路由层与服务层调用。

    判定规则:
        - role == "admin" 全通,无需查权限表。
        - role == "user" 时,设备 control 操作需在权限表中有记录。
        - 读操作(列表/详情/状态)不经过本服务,默认放行。
    """

    def __init__(
        self,
        repository: DevicePermissionRepository,
    ) -> None:
        """初始化权限服务。

        Args:
            repository: 设备权限仓储实例。
        """
        self._repository = repository

    def is_admin(self, user: dict | None) -> bool:
        """判断用户是否为管理员。

        Args:
            user: 当前用户文档。

        Returns:
            用户 role 为 admin 时返回 True。
        """
        return bool(user) and user.get("role") == "admin"

    def is_auth_enabled() -> bool:
        """Placeholder 静态方法,保留给未来扩展。"""
        return True

    def list_user_device_keys(self, user: dict | None) -> list[str]:
        """返回当前用户可控的设备标识列表。

        admin 返回空列表语义为"全部",由调用方自行解释。

        Args:
            user: 当前用户文档。

        Returns:
            设备标识列表(admin 返回空列表,代表不限制)。
        """
        if self.is_admin(user):
            return []
        if not user:
            return []
        return self._repository.list_device_keys_by_user(user["user_id"])

    def filter_allowed_device_keys(
        self,
        user: dict | None,
        device_keys: Iterable[str],
    ) -> list[str]:
        """从给定设备列表中过滤出当前用户有 control 权限的设备。

        Args:
            user: 当前用户文档。
            device_keys: 待过滤的设备标识集合。

        Returns:
            admin 时原样返回去重列表;普通用户返回有权限的子集。
        """
        unique_keys: list[str] = []
        seen: set[str] = set()
        for key in device_keys:
            if key and key not in seen:
                seen.add(key)
                unique_keys.append(key)

        if self.is_admin(user):
            return unique_keys
        if not user:
            return []

        allowed = set(
            self._repository.list_device_keys_by_user(user["user_id"])
        )
        return [key for key in unique_keys if key in allowed]

    def assert_control(
        self,
        user: dict | None,
        device_keys: Iterable[str],
    ) -> None:
        """断言用户对给定设备列表都有 control 权限,否则抛 403。

        Args:
            user: 当前用户文档。
            device_keys: 待校验的设备标识集合。

        Raises:
            HTTPException: 任一设备无权限时抛 403。
        """
        unique_keys = {
            key for key in device_keys if key
        }
        if not unique_keys:
            return

        if self.is_admin(user):
            return

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="未登录,无法执行设备控制操作。",
            )

        allowed = set(
            self._repository.list_device_keys_by_user(user["user_id"])
        )
        missing = unique_keys - allowed
        if missing:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"无设备控制权限: {','.join(sorted(missing))}",
            )

    def grant(
        self,
        user_id: str,
        device_key: str,
        granted_by: str,
    ) -> dict:
        """授予单个设备控制权限。

        Args:
            user_id: 被授权用户 ID。
            device_key: 设备唯一标识。
            granted_by: 授权人 user_id。

        Returns:
            授权记录。
        """
        return self._repository.grant(user_id, device_key, granted_by)

    def revoke(self, user_id: str, device_key: str) -> bool:
        """撤销单个设备控制权限。

        Args:
            user_id: 用户唯一 ID。
            device_key: 设备唯一标识。

        Returns:
            是否实际删除了记录。
        """
        return self._repository.revoke(user_id, device_key)

    def replace_user_devices(
        self,
        user_id: str,
        device_keys: list[str],
        granted_by: str,
    ) -> dict:
        """覆盖式更新某用户的可控设备集合。

        Args:
            user_id: 被授权用户 ID。
            device_keys: 新的设备标识完整列表。
            granted_by: 授权人 user_id。

        Returns:
            更新后的用户可控设备标识列表。
        """
        self._repository.replace_user_devices(user_id, device_keys, granted_by)
        return {
            "user_id": user_id,
            "device_keys": self._repository.list_device_keys_by_user(user_id),
        }

    def replace_device_users(
        self,
        device_key: str,
        user_ids: list[str],
        granted_by: str,
    ) -> dict:
        """覆盖式更新某设备的授权用户集合。

        Args:
            device_key: 设备唯一标识。
            user_ids: 新的用户 ID 完整列表。
            granted_by: 授权人 user_id。

        Returns:
            更新后的设备授权用户 ID 列表。
        """
        self._repository.replace_device_users(
            device_key, user_ids, granted_by
        )
        return {
            "device_key": device_key,
            "user_ids": self._repository.list_user_ids_by_device(device_key),
        }

    def list_grants_by_user(self, user_id: str) -> list[dict]:
        """返回某用户的全部授权记录。

        Args:
            user_id: 用户唯一 ID。

        Returns:
            授权记录列表。
        """
        return self._sanitize_grants(
            self._repository.list_grants_by_user(user_id)
        )

    def list_grants_by_device(self, device_key: str) -> list[dict]:
        """返回某设备的全部授权记录。

        Args:
            device_key: 设备唯一标识。

        Returns:
            授权记录列表。
        """
        return self._sanitize_grants(
            self._repository.list_grants_by_device(device_key)
        )

    @staticmethod
    def _sanitize_grants(grants: list[dict]) -> list[dict]:
        """整理授权记录格式,便于 JSON 序列化。

        Args:
            grants: 原始授权记录列表。

        Returns:
            整理后的授权记录列表。
        """
        result = []
        for item in grants:
            result.append(
                {
                    "user_id": item.get("user_id", ""),
                    "device_key": item.get("device_key", ""),
                    "permission_level": item.get(
                        "permission_level", "control"
                    ),
                    "granted_by": item.get("granted_by", ""),
                    "granted_at": item.get("granted_at"),
                }
            )
        return result
