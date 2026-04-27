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
    status_snapshot: DeviceStatusSnapshot = Field(default_factory=DeviceStatusSnapshot)


class DeviceListResponse(BaseModel):
    """设备列表响应。"""

    items: list[DeviceItem] = Field(default_factory=list)
