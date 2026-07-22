"""外部实验任务下发 Schema。"""

from typing import Any

from pydantic import BaseModel, Field


class ExternalExperimentObject(BaseModel):
    """实验对象信息。"""

    name: str = Field(min_length=1, max_length=200)
    type: str | None = Field(default=None, max_length=80)
    description: str | None = Field(default=None, max_length=2000)


class ExternalExperimentCondition(BaseModel):
    """外部下发的单组实验条件。"""

    condition_id: str = Field(min_length=1, max_length=120)
    parameters: dict[str, float | int | str] = Field(min_length=1)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ExternalExperimentDispatchCreateRequest(BaseModel):
    """创建外部实验任务批次请求。"""

    source_system: str = Field(min_length=1, max_length=80)
    source_module: str = Field(min_length=1, max_length=80)
    source_reference: dict[str, Any] = Field(default_factory=dict)
    experiment_name: str = Field(min_length=1, max_length=200)
    experiment_object: ExternalExperimentObject
    experiment_content: str | None = Field(default=None, max_length=10000)
    conditions: list[ExternalExperimentCondition] = Field(min_length=1, max_length=100)
    optimization_context: dict[str, Any] = Field(default_factory=dict)
    extra_metadata: dict[str, Any] = Field(default_factory=dict)


class ExternalExperimentDispatchCreateResponse(BaseModel):
    """创建外部实验任务批次响应。"""

    dispatch_id: str
    status: str = "received"
    received_at: str


class ExternalExperimentDispatchListItem(BaseModel):
    """外部实验任务列表项。"""

    dispatch_id: str
    status: str = "received"
    source_system: str
    source_module: str
    experiment_name: str
    experiment_object: ExternalExperimentObject
    condition_count: int = 0
    source_reference: dict[str, Any] = Field(default_factory=dict)
    received_at: str


class ExternalExperimentDispatchListResponse(BaseModel):
    """外部实验任务列表响应。"""

    items: list[ExternalExperimentDispatchListItem] = Field(default_factory=list)


class ExternalExperimentDispatchDetailResponse(
    ExternalExperimentDispatchListItem
):
    """外部实验任务详情响应。"""

    experiment_content: str | None = None
    conditions: list[ExternalExperimentCondition] = Field(default_factory=list)
    optimization_context: dict[str, Any] = Field(default_factory=dict)
    extra_metadata: dict[str, Any] = Field(default_factory=dict)
