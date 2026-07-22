"""外部服务调用 SpecLabOS 的统一鉴权依赖。"""

from fastapi import Header, HTTPException, status

from app.core.auth import parse_access_token
from app.core.config import get_settings
from app.repositories.identity_repository import UserRepository


def require_external_api_auth(
    authorization: str | None = Header(default=None),
) -> dict:
    """校验统一外部 API Token 或平台用户 Token。

    Args:
        authorization: HTTP Authorization 请求头。

    Returns:
        认证上下文字典，包含认证类型与用户信息。

    Raises:
        HTTPException: 缺少或提供无效认证信息时抛出 401。
    """
    settings = get_settings()
    api_token = settings.external_api.api_token
    auth_enabled = getattr(getattr(settings, "auth", None), "enabled", True)
    if not auth_enabled and not api_token:
        return {
            "auth_type": "dev",
            "user": {
                "user_id": "dev_admin",
                "username": "dev_admin",
                "role": "admin",
                "status": "active",
            },
        }

    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未提供认证信息。",
        )

    if api_token and authorization == f"Bearer {api_token}":
        return {"auth_type": "external_api_token", "user": None}

    token = authorization[7:] if authorization.startswith("Bearer ") else None
    payload = parse_access_token(token) if token else None
    if payload:
        user = UserRepository.find_by_user_id(payload["sub"])
        if user and user.get("status") == "active":
            return {"auth_type": "user", "user": user}

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="认证信息无效。",
    )
