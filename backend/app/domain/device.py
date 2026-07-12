"""设备资源领域模型。"""

from datetime import datetime

from pydantic import BaseModel, Field


class DeviceResource(BaseModel):
    """设备资源，替代现有 BaseDevice。

    设备不等于 IP，也不等于执行端电脑。
    一个设备可以有多种能力，通过 DeviceCapability 声明。
    """

    device_id: str
    name: str
    category: str
    device_type: str = ""
    location: str = ""
    enabled: bool = True
    sim_mode: bool = True
    connection: dict = Field(default_factory=dict)

    # 四维状态
    connection_status: str = "unknown"
    execution_status: str = "idle"
    data_status: str = "unknown"
    maintenance_status: str = "available"

    capabilities: list[str] = Field(default_factory=list)
    adapter_type: str | None = None
    status_sources: list[str] = Field(default_factory=list)
    status_updated_at: datetime | None = None
    status_message: str = ""
