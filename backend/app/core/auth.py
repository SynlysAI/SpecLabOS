"""统一登录 Token 生成、解析与当前用户获取。"""

import base64
import hashlib
import hmac
import json
import time
from typing import Optional

from fastapi import HTTPException, Request

from app.core.config import get_settings
from app.repositories.identity_repository import UserRepository


def _get_secret() -> bytes:
    """获取与 AI4MS 门户一致的 HMAC 签名密钥。"""
    secret = get_settings().auth.secret
    if not secret:
        raise HTTPException(status_code=500, detail="未配置统一认证密钥")
    return secret.encode("utf-8")


def generate_access_token(user_id: str, username: str, role: str) -> str:
    """生成统一登录 access token。

    Args:
        user_id: 用户唯一 ID。
        username: 用户名。
        role: 用户角色。

    Returns:
        与 AI4MS 兼容的自签名 token 字符串。
    """
    now = int(time.time())
    expire_hours = get_settings().auth.token_expire_hours
    payload = {
        "sub": user_id,
        "username": username,
        "role": role,
        "iat": now,
        "exp": now + expire_hours * 3600,
    }
    payload_b64 = base64.urlsafe_b64encode(
        json.dumps(payload, separators=(",", ":")).encode()
    ).rstrip(b"=").decode()
    sig = hmac.new(_get_secret(), payload_b64.encode(), hashlib.sha256).hexdigest()
    return f"{payload_b64}.{sig}"


def parse_access_token(token: str) -> Optional[dict]:
    """校验并解析统一登录 token。

    Args:
        token: 完整 token 字符串。

    Returns:
        校验通过时返回 payload 字典，否则返回 None。
    """
    try:
        payload_b64, sig = token.rsplit(".", 1)
    except (ValueError, AttributeError):
        return None

    expected_sig = hmac.new(_get_secret(), payload_b64.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected_sig, sig):
        return None

    try:
        padding = 4 - len(payload_b64) % 4
        if padding != 4:
            payload_b64 += "=" * padding
        payload = json.loads(base64.urlsafe_b64decode(payload_b64))
    except (TypeError, ValueError, json.JSONDecodeError):
        return None

    if payload.get("role") not in ("admin", "user"):
        return None
    if payload.get("exp", 0) < int(time.time()):
        return None
    return payload


def _extract_token(request: Request) -> Optional[str]:
    """从请求头提取 Bearer token。

    Args:
        request: 当前 HTTP 请求对象。

    Returns:
        提取到的 token，未提供时返回 None。
    """
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header[7:]
    return None


async def get_current_user_optional(request: Request) -> Optional[dict]:
    """可选获取当前登录用户。

    Args:
        request: 当前 HTTP 请求对象。

    Returns:
        已登录且账号有效时返回用户文档，否则返回 None。
    """
    if not get_settings().auth.enabled:
        return None

    token = _extract_token(request)
    if not token:
        return None
    payload = parse_access_token(token)
    if not payload:
        return None

    user = UserRepository.find_by_user_id(payload["sub"])
    return user if user and user.get("status") == "active" else None
