"""工作流服务。"""

from app.domain.models import WorkflowDefinitionCreate
from app.domain.enums import WorkflowRunStatus
from app.repositories.workflow_repository import WorkflowRepository


class WorkflowService:
    """封装工作流定义与运行创建逻辑。"""

    def __init__(self, workflow_repository: WorkflowRepository) -> None:
        """初始化工作流服务。

        Args:
            workflow_repository: 工作流仓储。
        """
        self._workflow_repository = workflow_repository

    def submit_definition(
        self,
        payload: WorkflowDefinitionCreate,
    ):
        """提交工作流定义并创建初始运行记录。

        Args:
            payload: 待提交的工作流定义。

        Returns:
            创建后的工作流定义与运行记录。
        """
        definition = self._workflow_repository.create_definition(payload)
        run = self._workflow_repository.create_run(definition)
        self._workflow_repository.mark_run_queued(run.run_id)
        run.status = WorkflowRunStatus.QUEUED
        return definition, run
