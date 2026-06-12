"""统一用户注册与登录业务逻辑。"""

import hashlib
import hmac
import os
from datetime import UTC, datetime

from app.core.auth import generate_access_token
from app.core.config import get_settings
from app.repositories.identity_repository import InviteCodeRepository, UserRepository


class AuthConfigurationError(RuntimeError):
    """统一认证配置错误。"""


def _ensure_auth_secret() -> None:
    """确认统一认证密钥已配置。"""
    if get_settings().auth.enabled and not get_settings().auth.secret:
        raise AuthConfigurationError("未配置统一认证密钥")


def _hash_password(password: str) -> str:
    """生成 PBKDF2-SHA256 密码哈希。

    Args:
        password: 明文密码。

    Returns:
        与 AI4MS 兼容的密码哈希字符串。
    """
    iterations = 260_000
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, iterations)
    return f"pbkdf2_sha256${iterations}${salt.hex()}${dk.hex()}"


def _verify_password(password: str, stored_hash: str) -> bool:
    """验证明文密码是否匹配存储哈希。

    Args:
        password: 明文密码。
        stored_hash: 数据库存储的密码哈希。

    Returns:
        匹配时返回 True，否则返回 False。
    """
    if "$" not in stored_hash:
        return hmac.compare_digest(
            hashlib.sha256(password.encode()).hexdigest(),
            stored_hash,
        )
    try:
        algo, iterations_str, salt_hex, hash_hex = stored_hash.split("$")
        if algo != "pbkdf2_sha256":
            return False
        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(hash_hex)
        dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, int(iterations_str))
        return hmac.compare_digest(dk, expected)
    except (TypeError, ValueError):
        return False


def _to_utc(value: datetime) -> datetime:
    """将数据库时间转换为 UTC aware datetime。

    Args:
        value: 数据库读取的时间。

    Returns:
        带 UTC 时区的时间。
    """
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _serialize_login_result(user: dict) -> dict:
    """序列化登录成功响应。

    Args:
        user: 用户文档。

    Returns:
        包含 token 和用户基础信息的字典。
    """
    token = generate_access_token(user["user_id"], user["username"], user["role"])
    return {
        "token": token,
        "user": {
            "user_id": user["user_id"],
            "username": user["username"],
            "role": user["role"],
            "organization": user.get("organization", ""),
        },
    }


def login(username: str, password: str) -> dict:
    """用户登录。

    Args:
        username: 用户名。
        password: 明文密码。

    Returns:
        包含 token 和用户信息的字典。

    Raises:
        ValueError: 用户名或密码错误，或用户不可用。
    """
    _ensure_auth_secret()
    user = UserRepository.find_by_username(username)
    if not user:
        raise ValueError("用户名或密码错误")
    if user.get("status") != "active":
        raise ValueError("用户已被禁用")
    if not _verify_password(password, user.get("password_hash", "")):
        raise ValueError("用户名或密码错误")

    UserRepository.update_login_time(user["user_id"])
    return _serialize_login_result(user)


def register(invite_code: str, username: str, password: str, organization: str = "") -> dict:
    """用户注册。

    Args:
        invite_code: AI4MS 门户生成的邀请码。
        username: 用户名。
        password: 明文密码。
        organization: 所属单位。

    Returns:
        包含 token 和用户信息的字典。

    Raises:
        ValueError: 注册参数无效或邀请码不可用。
    """
    _ensure_auth_secret()
    invite = InviteCodeRepository.find_by_code(invite_code)
    if not invite:
        raise ValueError("邀请码无效")
    if invite.get("status") != "active":
        raise ValueError("邀请码已失效")
    if _to_utc(invite["expires_at"]) < datetime.now(UTC):
        raise ValueError("邀请码已过期")
    if invite.get("used_count", 0) >= invite.get("max_uses", 0):
        raise ValueError("邀请码已用完")
    if UserRepository.find_by_username(username):
        raise ValueError("用户名已存在")

    updated = InviteCodeRepository.atomic_consume(invite["invite_id"])
    if updated is None:
        raise ValueError("邀请码已被使用或已过期")

    try:
        user = UserRepository.create(
            username=username,
            password_hash=_hash_password(password),
            role=invite["role"],
            organization=organization,
            created_by=invite.get("created_by"),
        )
    except Exception:
        InviteCodeRepository.rollback_usage(invite["invite_id"])
        raise

    UserRepository.update_login_time(user["user_id"])
    return _serialize_login_result(user)
