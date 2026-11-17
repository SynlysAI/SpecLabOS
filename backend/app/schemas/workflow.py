"""工作流相关 Schema。"""

from typing import Any

from pydantic import BaseModel, Field


class WorkflowItem(BaseModel):
    """工作流列表项。"""

    workflow_id: str
    name: str
    status: str = "pending"


class WorkflowListResponse(BaseModel):
    """工作流列表响应。"""

    items: list[WorkflowItem] = Field(default_factory=list)


class WorkflowStepCreateRequest(BaseModel):
    """工作流步骤创建请求。"""

    step_id: str
    device_key: str
    action_key: str
    display_name: str
    params: dict = Field(default_factory=dict)
    confirm_params: dict = Field(default_factory=dict)


class WorkflowCreateRequest(BaseModel):
    """工作流创建请求。"""

    name: str
    device_key: str
    description: str = ""
    created_by: str = "system"
    source: str = "manual"
    steps: list[WorkflowStepCreateRequest] = Field(default_factory=list)


class WorkflowRunItem(BaseModel):
    """工作流运行列表项。"""

    run_id: str
    workflow_name: str
    device_key: str = ""
    smartaccess_node_id: str = ""
    target_device_id: str = ""
    status: str = "pending"
    current_step_index: int = 0
    total_steps: int = 0
    started_at: str = "--"
    source: str = "speclabos"


class WorkflowRunListResponse(BaseModel):
    """工作流运行列表响应。"""

    items: list[WorkflowRunItem] = Field(default_factory=list)


class WorkflowRunStepItem(BaseModel):
    """工作流运行步骤项。"""

    name: str
    status: str = "idle"
    started_at: str = ""
    finished_at: str = ""
    description: str = ""
    params: dict = Field(default_factory=dict)
    result: Any = None


class WorkflowRunDataFileItem(BaseModel):
    """运行关联的数据文件项。"""

    file_id: str
    asset_id: str = ""
    filename: str = ""
    relative_path: str = ""
    asset_group_id: str = ""
    device_id: str = ""
    data_type: str = ""
    file_size: int = 0
    storage_uri: str = ""
    ingested_at: str = "--"
    bound: bool = False


class WorkflowRunDetailResponse(BaseModel):
    """工作流运行详情响应。"""

    run_id: str
    workflow_name: str
    status: str = "pending"
    current_step_index: int = 0
    total_steps: int = 0
    started_at: str = "--"
    finished_at: str = ""
    trigger_source: str = "manual"
    operator_name: str = "system"
    source: str = "speclabos"
    template_id: str = ""
    template_version: str = ""
    anchor_profile: str = ""
    smartaccess_node_id: str = ""
    target_device_id: str = ""
    events: list[dict] = Field(default_factory=list)
    steps: list[WorkflowRunStepItem] = Field(default_factory=list)
    # SmartAccess 运行的数据结果：已绑定文件与时间窗建议关联文件
    data_files: list[WorkflowRunDataFileItem] = Field(default_factory=list)
    data_suggestions: list[WorkflowRunDataFileItem] = Field(default_factory=list)


class WorkflowCreateResponse(BaseModel):
    """工作流创建响应。"""

    workflow_id: str
    run_id: str
