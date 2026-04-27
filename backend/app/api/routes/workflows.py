"""工作流接口路由。"""

from fastapi import APIRouter, Query

from app.schemas.workflow import (
    WorkflowListResponse,
    WorkflowRunDetailResponse,
    WorkflowRunListResponse,
)


router = APIRouter(prefix="/api/workflows", tags=["workflows"])

workflow_runs_router = APIRouter(prefix="/api/workflow-runs", tags=["workflow-runs"])


FALLBACK_WORKFLOW_ITEMS = [
    {
        "workflow_id": "wf-001",
        "name": "样品全流程分析",
        "status": "running",
    }
]

FALLBACK_RUN_ITEMS = [
    {
        "run_id": "RUN-20260427-001",
        "workflow_name": "样品全流程分析",
        "status": "running",
        "current_step_index": 2,
        "total_steps": 4,
        "started_at": "2026-04-27 10:15",
    },
    {
        "run_id": "RUN-20260427-002",
        "workflow_name": "核磁复测任务",
        "status": "warning",
        "current_step_index": 3,
        "total_steps": 3,
        "started_at": "2026-04-27 09:40",
    },
]

FALLBACK_RUN_DETAIL = {
    "run_id": "RUN-20260427-001",
    "workflow_name": "样品全流程分析",
    "status": "running",
    "current_step_index": 2,
    "total_steps": 4,
    "started_at": "2026-04-27 10:15",
    "finished_at": "",
    "trigger_source": "手动触发",
    "operator_name": "lab-admin",
    "steps": [
        {
            "name": "样品预检",
            "status": "online",
            "started_at": "2026-04-27 10:15",
            "finished_at": "2026-04-27 10:18",
            "description": "完成条码和收样状态核验。",
        },
        {
            "name": "仪器采集",
            "status": "running",
            "started_at": "2026-04-27 10:20",
            "finished_at": "",
            "description": "等待 LC-MS 上传原始谱图。",
        },
        {
            "name": "自动分析",
            "status": "idle",
            "started_at": "",
            "finished_at": "",
            "description": "采集完成后自动进入分析。",
        },
    ],
}


@router.get("", response_model=WorkflowListResponse)
def list_workflows() -> WorkflowListResponse:
    """返回工作流列表数据。"""
    return WorkflowListResponse(items=FALLBACK_WORKFLOW_ITEMS)


@workflow_runs_router.get("", response_model=WorkflowRunListResponse)
def list_workflow_runs(
    keyword: str | None = Query(default=None),
    status: str | None = Query(default=None),
) -> WorkflowRunListResponse:
    """返回工作流运行列表数据。"""
    filtered_items = FALLBACK_RUN_ITEMS
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
    return WorkflowRunDetailResponse(
        **{
            **FALLBACK_RUN_DETAIL,
            "run_id": run_id,
        }
    )
