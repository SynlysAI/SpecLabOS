"""设备相关 Schema。"""

from pydantic import BaseModel, Field


class DeviceStatusSnapshot(BaseModel):
    """设备状态快照。"""

    state: str = "idle"
    message: str = ""
    updated_at: str = "--"


class DeviceItem(BaseModel):
    """设备列表项。"""

    key: str
    name: str
    category: str
    device_type: str
    enabled: bool = True
    sim_mode: bool = True
    location: str = ""
    image_url: str | None = None
    connection: dict = Field(default_factory=dict)
    adapter_type: str = ""
    status_snapshot: DeviceStatusSnapshot = Field(default_factory=DeviceStatusSnapshot)


class DeviceListResponse(BaseModel):
    """设备列表响应。"""

    items: list[DeviceItem] = Field(default_factory=list)


class DeviceActionField(BaseModel):
    """设备动作字段定义。"""

    name: str
    type: str = "string"
    required: bool = False
    description: str = ""


class DeviceActionItem(BaseModel):
    """设备动作列表项。"""

    action_key: str
    name: str
    description: str
    step_mode: str = "single_step"
    parameter_schema: list[DeviceActionField] = Field(default_factory=list)


class DeviceActionListResponse(BaseModel):
    """设备动作列表响应。"""

    items: list[DeviceActionItem] = Field(default_factory=list)


class CameraFocusRequest(BaseModel):
    """镜头对焦请求参数。"""

    rt: int = 8000
    rb: int = 5000
    s: int = 3
