"""SmartAccess 集成接口。"""

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status

from app.core.config import get_settings
from app.runtime import get_smartaccess_service
from app.schemas.smartaccess import (
    SmartAccessRunCreateRequest,
    SmartAccessRunCreateResponse,
    SmartAccessRunEventRequest,
    SmartAccessRunListResponse,
    SmartAccessTemplateDetailResponse,
    SmartAccessTemplateItem,
    SmartAccessTemplateListResponse,
    SmartAccessTemplatePublishRequest,
)


def require_smartaccess_token(
    authorization: str | None = Header(default=None),
) -> None:
    """校验 SmartAccess 接口 Bearer Token。

    Args:
        authorization: HTTP Authorization 请求头。
    """
    api_token = get_settings().smartaccess.api_token
    if not api_token:
        return
    expected = f"Bearer {api_token}"
    if authorization != expected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="SmartAccess API token is invalid.",
        )


router = APIRouter(
    prefix="/api/smartaccess",
    tags=["smartaccess"],
    dependencies=[Depends(require_smartaccess_token)],
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


@router.post("/runs", response_model=SmartAccessRunCreateResponse)
def create_run(payload: SmartAccessRunCreateRequest) -> SmartAccessRunCreateResponse:
    """创建 SmartAccess 远程运行。"""
    run = get_smartaccess_service().create_run(payload)
    return SmartAccessRunCreateResponse(
        run_id=run["run_id"],
        status=run["status"],
    )


@router.get("/runs", response_model=SmartAccessRunListResponse)
def list_runs() -> SmartAccessRunListResponse:
    """查询 SmartAccess 运行列表。"""
    return SmartAccessRunListResponse(items=get_smartaccess_service().list_runs())


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
