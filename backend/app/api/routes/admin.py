"""管理员设备权限管理接口路由。"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.core.auth import require_admin
from app.repositories.identity_repository import UserRepository
from app.runtime import get_device_permission_service
from app.services.device_permission_service import DevicePermissionService


router = APIRouter(
    prefix="/api/admin",
    tags=["admin"],
    dependencies=[Depends(require_admin)],
)


class UserDeviceGrantRequest(BaseModel):
    """覆盖式设置用户可控设备请求体。"""

    device_keys: list[str] = Field(default_factory=list)


class DeviceUserGrantRequest(BaseModel):
    """覆盖式设置设备授权用户请求体。"""

    user_ids: list[str] = Field(default_factory=list)


class GrantItem(BaseModel):
    """单条授权记录。"""

    user_id: str
    device_key: str
    permission_level: str = "control"
    granted_by: str = ""
    granted_at: Optional[str] = None


class UserPermissionsResponse(BaseModel):
    """用户可控设备列表响应。"""

    user_id: str
    username: str
    role: str
    device_keys: list[str] = Field(default_factory=list)


class DevicePermissionsResponse(BaseModel):
    """设备授权用户列表响应。"""

    device_key: str
    user_ids: list[str] = Field(default_factory=list)


def _get_service() -> DevicePermissionService:
    """获取设备权限服务单例。"""
    return get_device_permission_service()


def _build_user_permissions(
    user_id: str, service: DevicePermissionService
) -> UserPermissionsResponse:
    """根据用户 ID 拼装用户权限响应。

    Args:
        user_id: 用户唯一 ID。
        service: 设备权限服务实例。

    Returns:
        用户权限响应对象。
    """
    user = UserRepository.find_by_user_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在。",
        )
    brief = UserRepository.serialize_user_brief(user)
    device_keys = service.list_user_device_keys(user)
    return UserPermissionsResponse(
        user_id=brief["user_id"],
        username=brief["username"],
        role=brief["role"],
        device_keys=device_keys,
    )


@router.get("/users")
def list_users() -> list[dict]:
    """返回全部用户列表(含角色与状态,用于权限管理页)。"""
    users = UserRepository.list_users()
    return [
        UserRepository.serialize_user_brief(user) for user in users
    ]


@router.get(
    "/users/{user_id}/devices",
    response_model=UserPermissionsResponse,
)
def get_user_devices(
    user_id: str,
    service: DevicePermissionService = Depends(_get_service),
) -> UserPermissionsResponse:
    """查询某用户可控的设备列表。"""
    return _build_user_permissions(user_id, service)


@router.put(
    "/users/{user_id}/devices",
    response_model=UserPermissionsResponse,
)
def replace_user_devices(
    user_id: str,
    payload: UserDeviceGrantRequest,
    admin: dict = Depends(require_admin),
    service: DevicePermissionService = Depends(_get_service),
) -> UserPermissionsResponse:
    """覆盖式设置某用户的可控设备集合。"""
    if not UserRepository.find_by_user_id(user_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在。",
        )
    service.replace_user_devices(
        user_id=user_id,
        device_keys=payload.device_keys,
        granted_by=admin["user_id"],
    )
    return _build_user_permissions(user_id, service)


@router.post(
    "/users/{user_id}/devices/{device_key}",
    response_model=UserPermissionsResponse,
)
def grant_user_device(
    user_id: str,
    device_key: str,
    admin: dict = Depends(require_admin),
    service: DevicePermissionService = Depends(_get_service),
) -> UserPermissionsResponse:
    """授予单个用户对单个设备的 control 权限(幂等)。"""
    if not UserRepository.find_by_user_id(user_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在。",
        )
    service.grant(
        user_id=user_id,
        device_key=device_key,
        granted_by=admin["user_id"],
    )
    return _build_user_permissions(user_id, service)


@router.delete(
    "/users/{user_id}/devices/{device_key}",
    response_model=UserPermissionsResponse,
)
def revoke_user_device(
    user_id: str,
    device_key: str,
    service: DevicePermissionService = Depends(_get_service),
) -> UserPermissionsResponse:
    """撤销单个用户对单个设备的 control 权限。"""
    service.revoke(user_id=user_id, device_key=device_key)
    return _build_user_permissions(user_id, service)


@router.get(
    "/devices/{device_key}/users",
    response_model=DevicePermissionsResponse,
)
def get_device_users(
    device_key: str,
    service: DevicePermissionService = Depends(_get_service),
) -> DevicePermissionsResponse:
    """查询某设备授权给了哪些用户。"""
    return DevicePermissionsResponse(
        device_key=device_key,
        user_ids=service._repository.list_user_ids_by_device(device_key),
    )


@router.put(
    "/devices/{device_key}/users",
    response_model=DevicePermissionsResponse,
)
def replace_device_users(
    device_key: str,
    payload: DeviceUserGrantRequest,
    admin: dict = Depends(require_admin),
    service: DevicePermissionService = Depends(_get_service),
) -> DevicePermissionsResponse:
    """覆盖式设置某设备的授权用户集合。"""
    service.replace_device_users(
        device_key=device_key,
        user_ids=payload.user_ids,
        granted_by=admin["user_id"],
    )
    return DevicePermissionsResponse(
        device_key=device_key,
        user_ids=service._repository.list_user_ids_by_device(device_key),
    )
