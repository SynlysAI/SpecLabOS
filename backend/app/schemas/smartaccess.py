"""SmartAccess 平台集成 Schema。"""

from typing import Any

from pydantic import BaseModel, Field


class SmartAccessTemplatePublishRequest(BaseModel):
    """SmartAccess 模板发布请求。"""

    template_id: str
    template_version: str
    workflow_id: str = ""
    name: str = ""
    description: str = ""
    anchor_profile: str = ""
    source_device_id: str = ""
    published_by: str = "smartaccess"
    workflow: dict[str, Any]


class SmartAccessTemplateItem(BaseModel):
    """SmartAccess 模板列表项。"""

    template_id: str
    template_version: str
    workflow_id: str = ""
    name: str = ""
    anchor_profile: str = ""
    source_device_id: str = ""
    status: str = "published"
    step_count: int = 0
    published_at: str = ""
    updated_at: str = ""


class SmartAccessTemplateListResponse(BaseModel):
    """SmartAccess 模板列表响应。"""

    items: list[SmartAccessTemplateItem] = Field(default_factory=list)


class SmartAccessTemplateDetailResponse(SmartAccessTemplateItem):
    """SmartAccess 模板详情响应。"""

    description: str = ""
    workflow: dict[str, Any] = Field(default_factory=dict)


class SmartAccessRunCreateRequest(BaseModel):
    """SmartAccess 远程运行创建请求。"""

    template_id: str
    template_version: str
    smartaccess_node_id: str
    target_device_id: str
    runtime_inputs: dict[str, str] = Field(default_factory=dict)
    requested_by: str = "system"


class SmartAccessRunCreateResponse(BaseModel):
    """SmartAccess 远程运行创建响应。"""

    run_id: str
    status: str = "queued"


class SmartAccessRunEventRequest(BaseModel):
    """SmartAccess 运行事件回传请求。"""

    event_id: str
    event_type: str
    status: str = ""
    step_id: str = ""
    step_index: int | None = None
    payload: dict[str, Any] = Field(default_factory=dict)


class SmartAccessRunItem(BaseModel):
    """SmartAccess 运行列表项。"""

    run_id: str
    workflow_name: str = ""
    device_key: str = ""
    smartaccess_node_id: str = ""
    target_device_id: str = ""
    status: str = "queued"
    current_step_index: int = 0
    total_steps: int = 0
    started_at: str = "--"
    source: str = "smartaccess"


class SmartAccessRunListResponse(BaseModel):
    """SmartAccess 运行列表响应。"""

    items: list[SmartAccessRunItem] = Field(default_factory=list)


class SmartAccessNodeHeartbeatRequest(BaseModel):
    """SmartAccess 执行端心跳上报请求。"""

    node_id: str
    device_info: dict[str, Any] = Field(default_factory=dict)
    heartbeat_interval_seconds: int = 30


class SmartAccessNodeItem(BaseModel):
    """SmartAccess 执行端节点列表项。"""

    node_id: str
    status: str = "offline"
    last_heartbeat_at: str = "--"
    first_seen_at: str = "--"
    seconds_since_heartbeat: float | None = None
    heartbeat_interval_seconds: int = 30
    device_info: dict[str, Any] = Field(default_factory=dict)


class SmartAccessNodeListResponse(BaseModel):
    """SmartAccess 执行端节点列表响应。"""

    items: list[SmartAccessNodeItem] = Field(default_factory=list)
