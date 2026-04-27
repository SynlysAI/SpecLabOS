"""领域枚举定义。"""

from enum import StrEnum


class WorkflowRunStatus(StrEnum):
    """工作流运行状态。"""

    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"


class StepRunStatus(StrEnum):
    """工作流步骤运行状态。"""

    PENDING = "pending"
    WAITING_DEVICE = "waiting_device"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"
