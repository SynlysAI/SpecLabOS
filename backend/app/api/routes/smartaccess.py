"""SmartAccess 集成接口。"""

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status

from app.core.auth import get_current_user_optional
from app.core.config import get_settings
from app.runtime import get_smartaccess_node_service, get_smartaccess_service
from app.schemas.smartaccess import (
    SmartAccessNodeHeartbeatRequest,
    SmartAccessNodeItem,
    SmartAccessNodeListResponse,
    SmartAccessRunCreateRequest,
    SmartAccessRunCreateResponse,
    SmartAccessRunEventRequest,
    SmartAccessRunListResponse,
    SmartAccessTemplateDetailResponse,
    SmartAccessTemplateItem,
    SmartAccessTemplateListResponse,
    SmartAccessTemplatePublishRequest,
)


def require_smartaccess_auth(
    authorization: str | None = Header(default=None),
) -> None:
    """校验 SmartAccess 接口认证，支持 API Token 或用户 Token。

    Args:
        authorization: HTTP Authorization 请求头。
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未提供认证信息。",
        )

    # 优先校验 API Token（供外部调用）
    api_token = get_settings().smartaccess.api_token
    if api_token and authorization == f"Bearer {api_token}":
        return

    # 其次校验用户 Token（供前端调用）
    from app.core.auth import parse_access_token

    token = authorization[7:] if authorization.startswith("Bearer ") else None
    if token and parse_access_token(token):
        return

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="认证信息无效。",
    )


router = APIRouter(
    prefix="/api/smartaccess",
    tags=["smartaccess"],
    dependencies=[Depends(require_smartaccess_auth)],
)


@router.post("/templates/publish", response_model=SmartAccessTemplateDetailResponse)
def publish_template(
    payload: SmartAccessTemplatePublishRequest,
) -> SmartAccessTemplateDetailResponse:
    """发布 SmartAccess 模板。"""
    return SmartAccessTemplateDetailResponse.model_validate(
        get_smartaccess_service().publish_template(payload)
    )


@router.get("/templates", response_model=SmartAccessTemplateListResponse)
def list_templates(
    keyword: str | None = Query(default=None),
    device_id: str | None = Query(default=None),
    status: str | None = Query(default=None),
) -> SmartAccessTemplateListResponse:
    """查询 SmartAccess 模板列表。"""
    records = get_smartaccess_service().list_templates(keyword, device_id, status)
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
def create_run(payload: SmartAccessRunCreateRequest) -> SmartAccessRunCreateResponse:
    """创建 SmartAccess 远程运行。"""
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


@router.get("/nodes", response_model=SmartAccessNodeListResponse)
def list_nodes() -> SmartAccessNodeListResponse:
    """查询 SmartAccess 执行端节点列表及在线状态。"""
    items = get_smartaccess_node_service().list_nodes()
    return SmartAccessNodeListResponse(
        items=[SmartAccessNodeItem.model_validate(item) for item in items]
    )
