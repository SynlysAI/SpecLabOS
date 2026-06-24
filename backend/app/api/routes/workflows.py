"""工作流接口路由。"""

from fastapi import APIRouter, HTTPException, Query

from app.core.datetime_utils import format_datetime
from app.domain.enums import WorkflowRunStatus
from app.domain.models import WorkflowDefinitionCreate, WorkflowStepDefinition
from app.runtime import get_smartaccess_service, get_workflow_repository
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
                    "started_at": format_datetime(
                        item.get("started_at") or item.get("created_at")
                    ),
                    "source": "speclabos",
                }
            )
    smartaccess_items = (
        get_smartaccess_service().list_runs()
        if source in (None, "", "smartaccess")
        else []
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
        return WorkflowRunDetailResponse.model_validate(
            get_smartaccess_service().get_run(run_id)
        )

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
        started_at=format_datetime(item.get("started_at") or item.get("created_at")),
        finished_at=format_datetime(item.get("finished_at"))
        if item.get("finished_at")
        else "",
        trigger_source=item.get("trigger_source", "manual"),
        operator_name=item.get("created_by", "system"),
        source="speclabos",
        steps=[
            {
                "name": step["display_name"],
                "status": step["status"],
                "started_at": format_datetime(step.get("started_at")) if step.get("started_at") else "",
                "finished_at": format_datetime(step.get("finished_at")) if step.get("finished_at") else "",
                "description": step.get("params", {}).get("description", ""),
                "params": step.get("params", {}),
                "result": step.get("result"),
            }
            for step in item.get("step_runs", [])
        ],
    )
