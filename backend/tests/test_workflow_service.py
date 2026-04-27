"""工作流仓储测试。"""

from app.domain.enums import WorkflowRunStatus
from app.domain.models import WorkflowDefinitionCreate
from app.repositories.workflow_repository import WorkflowRepository


def test_create_workflow_definition_and_run(fake_database) -> None:
    """验证工作流定义和运行记录可被创建。"""
    repository = WorkflowRepository(fake_database)

    definition = WorkflowDefinitionCreate(
        name="NMR 串行任务",
        description="测试工作流",
        source="manual",
        steps=[
            {
                "step_id": "step-1",
                "device_key": "nmr_2278",
                "action_key": "nmr.check_status",
                "params": {},
                "confirm_params": {},
                "display_name": "检查 NMR 状态",
            }
        ],
        tags=["nmr"],
        created_by="xiaoxu",
    )

    saved_definition = repository.create_definition(definition)
    saved_run = repository.create_run(saved_definition)
    stored_definition = fake_database["workflow_definitions"].find_one(
        {"workflow_id": saved_definition.workflow_id}
    )
    stored_run = fake_database["workflow_runs"].find_one(
        {"run_id": saved_run.run_id}
    )

    assert saved_definition.name == "NMR 串行任务"
    assert saved_run.workflow_id == saved_definition.workflow_id
    assert saved_run.workflow_name == saved_definition.name
    assert saved_run.status == WorkflowRunStatus.PENDING
    assert saved_run.total_steps == 1
    assert stored_definition is not None
    assert stored_definition["workflow_id"] == saved_definition.workflow_id
    assert stored_definition["name"] == "NMR 串行任务"
    assert "workflow_name" not in stored_definition
    assert stored_run is not None
    assert stored_run["workflow_id"] == saved_definition.workflow_id
    assert stored_run["workflow_name"] == "NMR 串行任务"
    assert stored_run["status"] == WorkflowRunStatus.PENDING
    assert stored_run["total_steps"] == 1
