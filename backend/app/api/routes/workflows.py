"""工作流接口路由。"""

from fastapi import APIRouter, HTTPException, Query

from app.core.mongo import get_database
from app.domain.enums import WorkflowRunStatus
from app.domain.models import WorkflowDefinitionCreate, WorkflowStepDefinition
from app.runtime import get_workflow_repository
from app.services.workflow_service import WorkflowService

from app.schemas.workflow import (
    WorkflowCreateRequest,
    WorkflowCreateResponse,
    WorkflowListResponse,
    WorkflowRunDetailResponse,
    WorkflowRunListResponse,
)


router = APIRouter(prefix="/api/workflows", tags=["workflows"])

workflow_runs_router = APIRouter(prefix="/api/workflow-runs", tags=["workflow-runs"])


def _get_workflow_service() -> WorkflowService:
    """构建工作流服务。"""
    return WorkflowService(get_workflow_repository())


def _format_datetime(value) -> str:
    """格式化运行时间字段。

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


def _build_smartaccess_steps(workflow_snapshot: dict, events: list[dict]) -> list[dict]:
    """根据 SmartAccess 工作流快照构造步骤信息。

    Args:
        workflow_snapshot: 工作流快照。
        events: 事件列表。

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

    steps = []
    for index, step in enumerate(workflow_steps):
        step_key = str(step.get("id") or step.get("step_id") or index)
        event = event_map.get(step_key) or event_map.get(str(index))
        steps.append(
            {
                "name": step.get("name")
                or step.get("display_name")
                or step.get("id")
                or step.get("step_id")
                or f"step-{index + 1}",
                "status": event.get("status", "queued") if event else "queued",
                "started_at": event.get("created_at", "") if event else "",
                "finished_at": "",
                "description": step.get("action", ""),
                "params": step,
                "result": event.get("payload") if event else None,
            }
        )
    return steps


def _list_smartaccess_runs() -> list[dict]:
    """读取 SmartAccess 运行列表。

    Returns:
        SmartAccess 运行列表项字典列表。
    """
    database = get_database()
    records = list(database["smartaccess_runs"].find({}).sort("requested_at", -1))
    return [
        {
            "run_id": item["run_id"],
            "workflow_name": item.get("workflow_name", ""),
            "device_key": item.get("device_id", ""),
            "status": item.get("status", "queued"),
            "current_step_index": int(item.get("current_step_index") or 0),
            "total_steps": int(item.get("total_steps") or 0),
            "started_at": _format_datetime(
                item.get("started_at") or item.get("requested_at")
            ),
            "source": "smartaccess",
        }
        for item in records
    ]


def _get_smartaccess_run_detail(run_id: str) -> WorkflowRunDetailResponse | None:
    """读取 SmartAccess 运行详情。

    Args:
        run_id: 平台运行 ID。

    Returns:
        SmartAccess 运行详情，不存在时返回 None。
    """
    database = get_database()
    record = database["smartaccess_runs"].find_one({"run_id": run_id})
    if record is None:
        return None
    events = [
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
        for item in (
            database["smartaccess_run_events"]
            .find({"run_id": run_id})
            .sort("created_at", 1)
        )
    ]
    workflow_snapshot = dict(record.get("workflow_snapshot") or {})
    return WorkflowRunDetailResponse(
        run_id=record["run_id"],
        workflow_name=record.get("workflow_name", ""),
        status=record.get("status", "queued"),
        current_step_index=int(record.get("current_step_index") or 0),
        total_steps=int(record.get("total_steps") or 0),
        started_at=_format_datetime(
            record.get("started_at") or record.get("requested_at")
        ),
        finished_at=_format_datetime(record.get("finished_at"))
        if record.get("finished_at")
        else "",
        trigger_source="smartaccess",
        operator_name=record.get("requested_by", "system"),
        source="smartaccess",
        template_id=record.get("template_id", ""),
        template_version=record.get("template_version", ""),
        anchor_profile=record.get("anchor_profile", ""),
        events=events,
        steps=_build_smartaccess_steps(workflow_snapshot, events),
    )


@router.get("", response_model=WorkflowListResponse)
def list_workflows() -> WorkflowListResponse:
    """返回工作流列表数据。"""
    repository = get_workflow_repository()
    items = []
    for item in repository.list_definitions():
        items.append(
            {
                "workflow_id": item["workflow_id"],
                "name": item["name"],
                "status": "draft",
            }
        )
    return WorkflowListResponse(items=items)


@router.post("", response_model=WorkflowCreateResponse)
def create_workflow(payload: WorkflowCreateRequest) -> WorkflowCreateResponse:
    """创建工作流定义并生成初始运行记录。"""
    invalid_steps = [
        step for step in payload.steps if step.device_key != payload.device_key
    ]
    if invalid_steps:
        raise HTTPException(status_code=400, detail="当前仅支持单设备工作流编排")

    workflow_service = _get_workflow_service()
    definition_payload = WorkflowDefinitionCreate(
        name=payload.name,
        description=payload.description,
        created_by=payload.created_by,
        source=payload.source,
        steps=[
            WorkflowStepDefinition(
                step_id=step.step_id,
                device_key=step.device_key,
                action_key=step.action_key,
                display_name=step.display_name,
                params=step.params,
                confirm_params=step.confirm_params,
            )
            for step in payload.steps
        ],
    )
    definition, run = workflow_service.submit_definition(definition_payload)
    return WorkflowCreateResponse(
        workflow_id=definition.workflow_id,
        run_id=run.run_id,
    )


@workflow_runs_router.get("", response_model=WorkflowRunListResponse)
def list_workflow_runs(
    keyword: str | None = Query(default=None),
    status: str | None = Query(default=None),
    source: str | None = Query(default=None),
) -> WorkflowRunListResponse:
    """返回工作流运行列表数据。"""
    speclabos_items = []
    if source in (None, "", "speclabos"):
        repository = get_workflow_repository()
        for item in repository.list_runs_by_status(
            [
                WorkflowRunStatus.PENDING.value,
                WorkflowRunStatus.QUEUED.value,
                WorkflowRunStatus.RUNNING.value,
                WorkflowRunStatus.SUCCESS.value,
                WorkflowRunStatus.FAILED.value,
                WorkflowRunStatus.CANCELLED.value,
            ]
        )[::-1]:
            speclabos_items.append(
                {
                    "run_id": item["run_id"],
                    "workflow_name": item["workflow_name"],
                    "device_key": (
                        item.get("step_runs", [{}])[0].get("device_key", "")
                        if item.get("step_runs")
                        else ""
                    ),
                    "status": item["status"],
                    "current_step_index": item.get("current_step_index", 0),
                    "total_steps": item.get("total_steps", 0),
                    "started_at": _format_datetime(
                        item.get("started_at") or item.get("created_at")
                    ),
                    "source": "speclabos",
                }
            )
    smartaccess_items = (
        _list_smartaccess_runs() if source in (None, "", "smartaccess") else []
    )
    filtered_items = speclabos_items + smartaccess_items
    if keyword:
        filtered_items = [
            {
                **item,
            }
            for item in filtered_items
            if keyword.lower() in item["run_id"].lower()
            or keyword.lower() in item["workflow_name"].lower()
        ]
    if status:
        filtered_items = [item for item in filtered_items if item["status"] == status]
    return WorkflowRunListResponse(items=filtered_items)


@workflow_runs_router.get("/{run_id}", response_model=WorkflowRunDetailResponse)
def get_workflow_run_detail(run_id: str) -> WorkflowRunDetailResponse:
    """返回单次工作流运行详情。"""
    if run_id.startswith("sa_run_"):
        detail = _get_smartaccess_run_detail(run_id)
        if detail is not None:
            return detail

    item = get_workflow_repository().get_run(run_id)
    if item is None:
        return WorkflowRunDetailResponse(
            run_id=run_id,
            workflow_name="未找到工作流",
            status=WorkflowRunStatus.CANCELLED.value,
            current_step_index=0,
            total_steps=0,
            trigger_source="manual",
            operator_name="system",
            source="speclabos",
            steps=[],
        )

    return WorkflowRunDetailResponse(
        run_id=item["run_id"],
        workflow_name=item["workflow_name"],
        status=item["status"],
        current_step_index=item.get("current_step_index", 0),
        total_steps=item.get("total_steps", 0),
        started_at=_format_datetime(item.get("started_at") or item.get("created_at")),
        finished_at=_format_datetime(item.get("finished_at"))
        if item.get("finished_at")
        else "",
        trigger_source=item.get("trigger_source", "manual"),
        operator_name=item.get("created_by", "system"),
        source="speclabos",
        steps=[
            {
                "name": step["display_name"],
                "status": step["status"],
                "started_at": step.get("started_at", "") or "",
                "finished_at": step.get("finished_at", "") or "",
                "description": step.get("params", {}).get("description", ""),
                "params": step.get("params", {}),
                "result": step.get("result"),
            }
            for step in item.get("step_runs", [])
        ],
    )
