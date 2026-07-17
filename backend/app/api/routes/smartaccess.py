"""SmartAccess 集成接口。"""

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status

from app.core.auth import parse_access_token
from app.core.config import get_settings
from app.repositories.identity_repository import UserRepository
from app.runtime import (
    get_device_permission_service,
    get_smartaccess_node_service,
    get_smartaccess_service,
)
from app.schemas.smartaccess import (
    SmartAccessNodeHeartbeatRequest,
    SmartAccessNodeItem,
    SmartAccessNodeListResponse,
    SmartAccessNodeRegisterRequest,
    SmartAccessRunCreateRequest,
    SmartAccessRunCreateResponse,
    SmartAccessRunEventRequest,
    SmartAccessRunListResponse,
    SmartAccessTemplateDetailResponse,
    SmartAccessTemplateItem,
    SmartAccessTemplateListResponse,
    SmartAccessTemplatePublishRequest,
)
from app.services.device_permission_service import DevicePermissionService


SMARTACCESS_DEVICE_PREFIX = "smartaccess:"


def require_smartaccess_auth(
    authorization: str | None = Header(default=None),
) -> dict:
    """校验 SmartAccess 接口认证，支持 API Token 或用户 Token。

    Args:
        authorization: HTTP Authorization 请求头。

    Returns:
        认证上下文字典，包含认证类型与当前用户信息。
    """
    settings = get_settings()
    api_token = settings.smartaccess.api_token
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

    # 优先校验 API Token（供外部调用）
    if api_token and authorization == f"Bearer {api_token}":
        return {"auth_type": "api_token", "user": None}

    # 其次校验用户 Token（供前端调用）
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


def _get_permission_service() -> DevicePermissionService:
    """获取设备权限服务单例。"""
    return get_device_permission_service()


def _build_smartaccess_device_key(target_device_id: str) -> str:
    """构造 SmartAccess 虚拟设备权限标识。

    Args:
        target_device_id: SmartAccess 目标设备标识。

    Returns:
        用于设备权限表校验的虚拟设备标识。
    """
    if target_device_id.startswith(SMARTACCESS_DEVICE_PREFIX):
        return target_device_id
    return f"{SMARTACCESS_DEVICE_PREFIX}{target_device_id}"


def _resolve_template_device_key(payload: SmartAccessTemplatePublishRequest) -> str:
    """解析模板发布对应的 SmartAccess 虚拟设备权限标识。

    Args:
        payload: SmartAccess 模板发布请求。

    Returns:
        用于设备权限表校验和授权的虚拟设备标识。
    """
    device_id = (
        payload.source_device_id
        or payload.anchor_profile
        or payload.template_id
        or ""
    )
    return _build_smartaccess_device_key(device_id) if device_id else ""


def _grant_first_publisher_control(
    payload: SmartAccessTemplatePublishRequest,
    auth_context: dict,
    permission_service: DevicePermissionService,
) -> None:
    """普通用户首次发布 SmartAccess 设备时自动获得控制权限。

    Args:
        payload: SmartAccess 模板发布请求。
        auth_context: SmartAccess 接口认证上下文。
        permission_service: 设备权限服务。
    """
    user = auth_context.get("user")
    if auth_context.get("auth_type") != "user" or permission_service.is_admin(user):
        return

    device_key = _resolve_template_device_key(payload)
    if not device_key:
        return
    if permission_service.list_grants_by_device(device_key):
        return
    permission_service.grant(user["user_id"], device_key, user["user_id"])


router = APIRouter(
    prefix="/api/smartaccess",
    tags=["smartaccess"],
    dependencies=[Depends(require_smartaccess_auth)],
)


@router.post("/templates/publish", response_model=SmartAccessTemplateDetailResponse)
def publish_template(
    payload: SmartAccessTemplatePublishRequest,
    auth_context: dict = Depends(require_smartaccess_auth),
    permission_service: DevicePermissionService = Depends(_get_permission_service),
) -> SmartAccessTemplateDetailResponse:
    """发布 SmartAccess 模板。"""
    template = get_smartaccess_service().publish_template(payload)
    _grant_first_publisher_control(payload, auth_context, permission_service)
    return SmartAccessTemplateDetailResponse.model_validate(template)


@router.get("/templates", response_model=SmartAccessTemplateListResponse)
def list_templates(
    keyword: str | None = Query(default=None),
    device_id: str | None = Query(default=None),
    source_device_id: str | None = Query(default=None),
    status: str | None = Query(default=None),
) -> SmartAccessTemplateListResponse:
    """查询 SmartAccess 模板列表。"""
    records = get_smartaccess_service().list_templates(
        keyword,
        device_id,
        source_device_id,
        status,
    )
    return SmartAccessTemplateListResponse(
        items=[SmartAccessTemplateItem.model_validate(item) for item in records]
    )


@router.get(
    "/templates/{template_id}/versions/{template_version}",
    response_model=SmartAccessTemplateDetailResponse,
)
def get_template(
    template_id: str,
    template_version: str,
) -> SmartAccessTemplateDetailResponse:
    """读取 SmartAccess 模板详情。"""
    return SmartAccessTemplateDetailResponse.model_validate(
        get_smartaccess_service().get_template(template_id, template_version)
    )


@router.delete("/templates/{template_id}/versions/{template_version}")
def delete_template(
    template_id: str,
    template_version: str,
) -> dict:
    """删除 SmartAccess 模板。"""
    get_smartaccess_service().delete_template(template_id, template_version)
    return {"detail": "模板已删除"}


@router.post("/runs", response_model=SmartAccessRunCreateResponse)
def create_run(
    payload: SmartAccessRunCreateRequest,
    auth_context: dict = Depends(require_smartaccess_auth),
    permission_service: DevicePermissionService = Depends(_get_permission_service),
) -> SmartAccessRunCreateResponse:
    """创建 SmartAccess 远程运行。"""
    if auth_context.get("auth_type") == "user":
        permission_service.assert_control(
            auth_context.get("user"),
            [_build_smartaccess_device_key(payload.target_device_id)],
        )
    run = get_smartaccess_service().create_run(payload)
    return SmartAccessRunCreateResponse(
        run_id=run["run_id"],
        status=run["status"],
    )


@router.get("/runs", response_model=SmartAccessRunListResponse)
def list_runs(
    keyword: str | None = Query(default=None),
    status: str | None = Query(default=None),
) -> SmartAccessRunListResponse:
    """查询 SmartAccess 运行列表。"""
    records = get_smartaccess_service().list_runs()
    if keyword:
        needle = keyword.lower()
        records = [
            item for item in records
            if needle in item.get("run_id", "").lower()
            or needle in item.get("workflow_name", "").lower()
        ]
    if status:
        records = [item for item in records if item.get("status") == status]
    return SmartAccessRunListResponse(items=records)


@router.get("/runs/{run_id}")
def get_run(run_id: str) -> dict:
    """读取 SmartAccess 运行详情。"""
    return get_smartaccess_service().get_run(run_id)


@router.post("/runs/{run_id}/events")
def append_event(run_id: str, payload: SmartAccessRunEventRequest) -> dict:
    """接收 SmartAccess 运行事件。"""
    event = get_smartaccess_service().append_event(run_id, payload)
    return {
        "event_id": event.get("event_id", ""),
        "run_id": event.get("run_id", ""),
        "event_type": event.get("event_type", ""),
        "step_id": event.get("step_id", ""),
        "step_index": event.get("step_index"),
        "status": event.get("status", ""),
        "payload": event.get("payload", {}),
        "created_at": event.get("created_at", ""),
    }


@router.post("/nodes/heartbeat")
def receive_node_heartbeat(payload: SmartAccessNodeHeartbeatRequest) -> dict:
    """接收 SmartAccess 执行端心跳上报。"""
    record = get_smartaccess_node_service().receive_heartbeat(
        payload.node_id,
        device_info=payload.device_info,
        heartbeat_interval_seconds=payload.heartbeat_interval_seconds,
    )
    return {
        "status": "ok",
        "node_id": record.get("node_id", payload.node_id),
        "node_status": record.get("status", "online"),
    }


@router.post("/nodes/register")
def register_node(payload: SmartAccessNodeRegisterRequest) -> dict:
    """注册并校验 SmartAccess 执行端节点身份。"""

    result = get_smartaccess_node_service().register_node(
        payload.node_id,
        machine_fingerprint=payload.machine_fingerprint,
        device_info=payload.device_info,
    )
    if result.get("conflict"):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "message": "SMARTACCESS_DEVICE_ID 已被另一台电脑注册",
                **result,
            },
        )
    return result


@router.get("/nodes", response_model=SmartAccessNodeListResponse)
def list_nodes() -> SmartAccessNodeListResponse:
    """查询 SmartAccess 执行端节点列表及在线状态。"""
    items = get_smartaccess_node_service().list_nodes()
    return SmartAccessNodeListResponse(
        items=[SmartAccessNodeItem.model_validate(item) for item in items]
    )
