"""统一认证接口路由。"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.core.auth import get_current_user_optional
from app.core.config import get_settings
from app.services.auth_service import AuthConfigurationError, login, register

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


class LoginRequest(BaseModel):
    """登录请求体。"""

    username: str
    password: str


class RegisterRequest(BaseModel):
    """注册请求体。"""

    invite_code: str
    username: str
    password: str
    organization: str = ""


class AuthResponse(BaseModel):
    """认证接口统一响应体。"""

    code: int = 0
    message: str = "成功"
    data: dict


@router.post("/login", response_model=AuthResponse)
async def login_endpoint(payload: LoginRequest) -> AuthResponse:
    """用户登录。

    Args:
        payload: 登录请求参数。

    Returns:
        认证成功响应。
    """
    try:
        return AuthResponse(data=login(payload.username, payload.password))
    except AuthConfigurationError as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc))


@router.post("/register", response_model=AuthResponse)
async def register_endpoint(payload: RegisterRequest) -> AuthResponse:
    """用户注册。

    Args:
        payload: 注册请求参数。

    Returns:
        注册成功响应。
    """
    try:
        return AuthResponse(
            data=register(
                payload.invite_code,
                payload.username,
                payload.password,
                payload.organization,
            )
        )
    except AuthConfigurationError as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/me")
async def get_me(user: dict | None = Depends(get_current_user_optional)) -> dict:
    """获取当前登录用户状态。

    Args:
        user: 当前用户文档。

    Returns:
        当前鉴权配置和用户基础信息。
    """
    user_info = None
    if user:
        user_info = {
            "user_id": user["user_id"],
            "username": user["username"],
            "role": user["role"],
            "status": user.get("status", "active"),
            "organization": user.get("organization", ""),
        }
    return {
        "code": 0,
        "message": "成功",
        "data": {
            "auth_enabled": get_settings().auth.enabled,
            "user": user_info,
        },
    }
