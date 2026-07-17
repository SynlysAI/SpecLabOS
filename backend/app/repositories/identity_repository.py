"""统一用户与邀请码数据仓储。"""

import secrets
from datetime import UTC, datetime
from typing import Optional

import mongomock
from pymongo import MongoClient, ReturnDocument
from pymongo.collection import Collection
from pymongo.errors import DuplicateKeyError, OperationFailure, ServerSelectionTimeoutError

from app.core.config import get_settings

_USER_CLIENT: MongoClient | None = None


def _gen_id(prefix: str) -> str:
    """生成带业务前缀的随机 ID。

    Args:
        prefix: ID 前缀。

    Returns:
        拼接前缀后的随机 ID。
    """
    return f"{prefix}_{secrets.token_hex(6)}"


def _get_user_client() -> MongoClient:
    """创建并缓存统一用户库 MongoDB 客户端。

    Returns:
        可用的 MongoDB 客户端。
    """
    global _USER_CLIENT
    if _USER_CLIENT is not None:
        return _USER_CLIENT

    settings = get_settings()
    uri = settings.auth.user_mongo_uri or settings.mongo.uri
    client = MongoClient(uri, serverSelectionTimeoutMS=1000)
    try:
        client.admin.command("ping")
        _USER_CLIENT = client
    except ServerSelectionTimeoutError:
        _USER_CLIENT = mongomock.MongoClient()
    return _USER_CLIENT


def _get_identity_collection(name: str) -> Collection:
    """获取统一用户库集合。

    Args:
        name: 集合名称。

    Returns:
        指定集合对象。
    """
    database = get_settings().auth.user_database
    collection = _get_user_client()[database].get_collection(name)
    try:
        collection.create_index("username" if name == "users" else "invite_code", unique=True)
    except OperationFailure as exc:
        if exc.code != 85:
            raise
    return collection


class UserRepository:
    """统一用户数据访问层。"""

    @staticmethod
    def get_collection() -> Collection:
        """获取 users 集合。

        Returns:
            users 集合对象。
        """
        return _get_identity_collection("users")

    @staticmethod
    def find_by_username(username: str) -> Optional[dict]:
        """按用户名查询用户。

        Args:
            username: 用户名。

        Returns:
            用户文档或 None。
        """
        return UserRepository.get_collection().find_one({"username": username})

    @staticmethod
    def find_by_user_id(user_id: str) -> Optional[dict]:
        """按用户 ID 查询用户。

        Args:
            user_id: 用户 ID。

        Returns:
            用户文档或 None。
        """
        return UserRepository.get_collection().find_one({"user_id": user_id})

    @staticmethod
    def create(
        username: str,
        password_hash: str,
        role: str,
        organization: str,
        created_by: Optional[str],
    ) -> dict:
        """创建用户。

        Args:
            username: 用户名。
            password_hash: 密码哈希。
            role: 用户角色。
            organization: 所属单位。
            created_by: 创建者用户 ID。

        Returns:
            已创建的用户文档。
        """
        now = datetime.now(UTC)
        doc = {
            "user_id": _gen_id("u"),
            "username": username,
            "password_hash": password_hash,
            "role": role,
            "status": "active",
            "organization": organization,
            "created_at": now,
            "updated_at": now,
            "last_login_at": None,
            "created_by": created_by,
        }
        try:
            UserRepository.get_collection().insert_one(doc)
        except DuplicateKeyError:
            raise ValueError("用户名已存在")
        return doc

    @staticmethod
    def update_login_time(user_id: str) -> None:
        """更新用户最后登录时间。

        Args:
            user_id: 用户 ID。
        """
        now = datetime.now(UTC)
        UserRepository.get_collection().update_one(
            {"user_id": user_id},
            {"$set": {"last_login_at": now, "updated_at": now}},
        )

    @staticmethod
    def list_users() -> list[dict]:
        """返回全部用户(管理员视角,不含密码字段)。

        Returns:
            用户摘要信息列表,按创建时间倒序。
        """
        cursor = (
            UserRepository.get_collection()
            .find({}, {"password_hash": 0})
            .sort("created_at", -1)
        )
        return list(cursor)

    @staticmethod
    def serialize_user_brief(user: dict) -> dict:
        """整理用户摘要字段,便于 JSON 序列化。

        Args:
            user: 用户文档。

        Returns:
            仅含摘要字段的用户字典。
        """
        if not user:
            return {}
        return {
            "user_id": user.get("user_id", ""),
            "username": user.get("username", ""),
            "role": user.get("role", "user"),
            "status": user.get("status", "active"),
            "organization": user.get("organization", ""),
            "created_at": user.get("created_at"),
            "last_login_at": user.get("last_login_at"),
        }


class InviteCodeRepository:
    """统一邀请码数据访问层。"""

    @staticmethod
    def get_collection() -> Collection:
        """获取 invite_codes 集合。

        Returns:
            invite_codes 集合对象。
        """
        return _get_identity_collection("invite_codes")

    @staticmethod
    def find_by_code(invite_code: str) -> Optional[dict]:
        """按邀请码查询记录。

        Args:
            invite_code: 邀请码。

        Returns:
            邀请码文档或 None。
        """
        return InviteCodeRepository.get_collection().find_one({"invite_code": invite_code})

    @staticmethod
    def atomic_consume(invite_id: str) -> Optional[dict]:
        """原子消费邀请码。

        Args:
            invite_id: 邀请码 ID。

        Returns:
            消费后的邀请码文档；无可用次数时返回 None。
        """
        now = datetime.now(UTC)
        return InviteCodeRepository.get_collection().find_one_and_update(
            {
                "invite_id": invite_id,
                "status": "active",
                "expires_at": {"$gt": now},
                "$expr": {"$lt": ["$used_count", "$max_uses"]},
            },
            {"$inc": {"used_count": 1}, "$set": {"updated_at": now}},
            return_document=ReturnDocument.AFTER,
        )

    @staticmethod
    def rollback_usage(invite_id: str) -> None:
        """回滚邀请码使用次数。

        Args:
            invite_id: 邀请码 ID。
        """
        InviteCodeRepository.get_collection().update_one(
            {"invite_id": invite_id, "used_count": {"$gt": 0}},
            {"$inc": {"used_count": -1}},
        )
