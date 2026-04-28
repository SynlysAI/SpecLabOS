"""工作流接口路由。"""

from datetime import datetime

from app.core.mongo import get_database
from app.domain.enums import WorkflowRunStatus
from app.domain.models import WorkflowDefinitionCreate, WorkflowStepDefinition
from app.repositories.workflow_repository import WorkflowRepository
from app.services.workflow_service import WorkflowService
from fastapi import APIRouter, Query

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
    repository = WorkflowRepository(get_database())
    return WorkflowService(repository)


@router.get("", response_model=WorkflowListResponse)
def list_workflows() -> WorkflowListResponse:
    """返回工作流列表数据。"""
    database = get_database()
    items = []
    for item in database["workflow_definitions"].find().sort("created_at", -1):
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
    database = get_database()
    database["workflow_runs"].update_one(
        {"run_id": run.run_id},
        {
            "$set": {
                "status": WorkflowRunStatus.RUNNING.value,
                "current_step_index": 1 if run.total_steps else 0,
                "started_at": datetime.utcnow(),
                "step_runs.0.status": "running" if run.total_steps else "pending",
                "step_runs.0.started_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M")
                if run.total_steps
                else "",
            }
        },
    )
    return WorkflowCreateResponse(
        workflow_id=definition.workflow_id,
        run_id=run.run_id,
    )


@workflow_runs_router.get("", response_model=WorkflowRunListResponse)
def list_workflow_runs(
    keyword: str | None = Query(default=None),
    status: str | None = Query(default=None),
) -> WorkflowRunListResponse:
    """返回工作流运行列表数据。"""
    database = get_database()
    filtered_items = []
    for item in database["workflow_runs"].find().sort("created_at", -1):
        filtered_items.append(
            {
                "run_id": item["run_id"],
                "workflow_name": item["workflow_name"],
                "status": item["status"],
                "current_step_index": item.get("current_step_index", 0),
                "total_steps": item.get("total_steps", 0),
                "started_at": (
                    item.get("started_at") or item.get("created_at")
                ).strftime("%Y-%m-%d %H:%M")
                if item.get("created_at") or item.get("started_at")
                else "--",
            }
        )
    if keyword:
        filtered_items = [
            item
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
    database = get_database()
    item = database["workflow_runs"].find_one({"run_id": run_id})
    if item is None:
        return WorkflowRunDetailResponse(
            run_id=run_id,
            workflow_name="未找到工作流",
            status=WorkflowRunStatus.CANCELLED.value,
            current_step_index=0,
            total_steps=0,
            trigger_source="manual",
            operator_name="system",
            steps=[],
        )

    return WorkflowRunDetailResponse(
        run_id=item["run_id"],
        workflow_name=item["workflow_name"],
        status=item["status"],
        current_step_index=item.get("current_step_index", 0),
        total_steps=item.get("total_steps", 0),
        started_at=(
            item.get("started_at") or item.get("created_at")
        ).strftime("%Y-%m-%d %H:%M")
        if item.get("created_at") or item.get("started_at")
        else "--",
        finished_at=item.get("finished_at", "") or "",
        trigger_source=item.get("trigger_source", "manual"),
        operator_name=item.get("created_by", "system"),
        steps=[
            {
                "name": step["display_name"],
                "status": step["status"],
                "started_at": step.get("started_at", "") or "",
                "finished_at": step.get("finished_at", "") or "",
                "description": step.get("params", {}).get("description", ""),
            }
            for step in item.get("step_runs", [])
        ],
    )
