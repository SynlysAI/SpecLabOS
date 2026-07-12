"""运行事件领域模型。"""

from datetime import datetime, timezone
from enum import StrEnum
from uuid import uuid4

from pydantic import BaseModel, Field


class RunEventType(StrEnum):
    """运行事件类型。"""

    QUEUED = "queued"
    ACCEPTED = "accepted"
    RUNNING = "running"
    STEP_STARTED = "step_started"
    STEP_COMPLETED = "step_completed"
    STEP_FAILED = "step_failed"
    FINISHED = "finished"
    FAILED = "failed"
    CANCELLED = "cancelled"


class RunEvent(BaseModel):
    """运行过程事件。

    借鉴 Dagster DagsterEvent，所有状态变更通过事件记录。
    事件是不可变的追加日志，支持完整审计追溯。
    """

    event_id: str = Field(default_factory=lambda: str(uuid4()))
    run_id: str
    event_type: RunEventType
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    step_key: str | None = None
    device_id: str | None = None
    adapter_type: str | None = None
    payload: dict = Field(default_factory=dict)
    message: str = ""
