"""SmartAccess 集成接口。"""

from fastapi import APIRouter, HTTPException, Query

from app.core.mongo import get_database
from app.runtime import get_smartaccess_service
from app.schemas.smartaccess import (
    SmartAccessRunCreateRequest,
    SmartAccessRunCreateResponse,
    SmartAccessRunEventRequest,
    SmartAccessRunItem,
    SmartAccessRunListResponse,
    SmartAccessTemplateDetailResponse,
    SmartAccessTemplateItem,
    SmartAccessTemplateListResponse,
    SmartAccessTemplatePublishRequest,
)


router = APIRouter(prefix="/api/smartaccess", tags=["smartaccess"])


def _format_datetime(value) -> str:
    """格式化时间字段。

    Args:
        value: 原始时间值。

    Returns:
        格式化后的时间字符串。
    """
    if value is None:
        return "--"
    if hasattr(value, "strftime"):
        return value.strftime("%Y-%m-%d %H:%M")
    return str(value)


def _list_run_events(run_id: str) -> list[dict]:
    """读取指定运行的事件列表。

    Args:
        run_id: 平台运行 ID。

    Returns:
        事件记录列表。
    """
    database = get_database()
    events = []
    for item in (
        database["smartaccess_run_events"]
        .find({"run_id": run_id})
        .sort("created_at", 1)
    ):
        events.append(
            {
                "event_id": item.get("event_id", ""),
                "run_id": item.get("run_id", ""),
                "event_type": item.get("event_type", ""),
                "step_id": item.get("step_id", ""),
                "step_index": item.get("step_index"),
                "status": item.get("status", ""),
                "payload": item.get("payload", {}),
                "created_at": item.get("created_at", ""),
            }
        )
    return events


def _build_steps_from_workflow(
    workflow_snapshot: dict,
    events: list[dict],
) -> list[dict]:
    """根据工作流快照和事件构造步骤详情。

    Args:
        workflow_snapshot: 工作流快照。
        events: 事件记录列表。

    Returns:
        步骤详情列表。
    """
    workflow_steps = workflow_snapshot.get("steps", [])
    event_map: dict[str, dict] = {}
    for item in events:
        step_key = item.get("step_id")
        if not step_key and item.get("step_index") is not None:
            step_key = str(item.get("step_index"))
        if step_key:
            event_map[step_key] = item

    items = []
    for index, step in enumerate(workflow_steps):
        step_key = str(step.get("id") or step.get("step_id") or index)
        event = event_map.get(step_key) or event_map.get(str(index))
        items.append(
            {
                "name": step.get("name")
                or step.get("display_name")
                or step.get("id")
                or step.get("step_id")
                or f"step-{index + 1}",
                "status": (
                    event.get("status")
                    if event
                    else (
                        "running"
                        if index < int(workflow_snapshot.get("current_step_index", 0))
                        else "queued"
                    )
                ),
                "started_at": event.get("created_at", "") if event else "",
                "finished_at": "",
                "description": step.get("action", ""),
                "params": step,
                "result": event.get("payload") if event else None,
            }
        )
    return items


def _build_run_item(record: dict) -> SmartAccessRunItem:
    """将运行记录转换为列表项。

    Args:
        record: 运行记录。

    Returns:
        运行列表项。
    """
    return SmartAccessRunItem(
        run_id=record["run_id"],
        workflow_name=record.get("workflow_name", ""),
        device_key=record.get("device_id", ""),
        status=record.get("status", "queued"),
        current_step_index=int(record.get("current_step_index") or 0),
        total_steps=int(record.get("total_steps") or 0),
        started_at=_format_datetime(
            record.get("started_at") or record.get("requested_at")
        ),
        source="smartaccess",
    )


def _build_run_detail(record: dict) -> dict:
    """将运行记录转换为详情响应。

    Args:
        record: 运行记录。

    Returns:
        运行详情响应字典。
    """
    events = _list_run_events(record["run_id"])
    workflow_snapshot = dict(record.get("workflow_snapshot") or {})
    workflow_snapshot["current_step_index"] = int(
        record.get("current_step_index") or 0
    )
    return {
        "run_id": record["run_id"],
        "workflow_name": record.get("workflow_name", ""),
        "status": record.get("status", "queued"),
        "current_step_index": int(record.get("current_step_index") or 0),
        "total_steps": int(record.get("total_steps") or 0),
        "started_at": _format_datetime(
            record.get("started_at") or record.get("requested_at")
        ),
        "finished_at": _format_datetime(record.get("finished_at"))
        if record.get("finished_at")
        else "",
        "trigger_source": "smartaccess",
        "operator_name": record.get("requested_by", "system"),
        "source": "smartaccess",
        "template_id": record.get("template_id", ""),
        "template_version": record.get("template_version", ""),
        "anchor_profile": record.get("anchor_profile", ""),
        "events": events,
        "steps": _build_steps_from_workflow(workflow_snapshot, events),
    }


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
    database = get_database()
    records = list(database["smartaccess_runs"].find({}).sort("requested_at", -1))
    return SmartAccessRunListResponse(
        items=[_build_run_item(item) for item in records]
    )


@router.get("/runs/{run_id}")
def get_run(run_id: str) -> dict:
    """读取 SmartAccess 运行详情。"""
    database = get_database()
    record = database["smartaccess_runs"].find_one({"run_id": run_id})
    if record is None:
        raise HTTPException(status_code=404, detail="SmartAccess 运行不存在")
    return _build_run_detail(record)


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
