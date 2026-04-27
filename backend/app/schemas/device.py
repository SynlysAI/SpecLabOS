"""设备相关 Schema。"""

from pydantic import BaseModel, Field


class DeviceItem(BaseModel):
    """设备列表项。"""

    key: str
    name: str
    status: str = "idle"


class DeviceListResponse(BaseModel):
    """设备列表响应。"""

    items: list[DeviceItem] = Field(default_factory=list)
