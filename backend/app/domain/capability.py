"""设备能力声明领域模型。"""

from pydantic import BaseModel, Field


class DeviceCapability(BaseModel):
    """设备可执行能力声明。

    一个设备可以有多种能力（如 NMR 可以跑实验、查状态、校准）。
    能力声明包含输入参数 schema 和结果 schema，支持自动校验和下游消费。
    """

    capability_key: str
    device_category: str
    name: str
    description: str = ""
    step_mode: str = "auto"
    parameter_schema: dict = Field(default_factory=dict)
    result_schema: dict = Field(default_factory=dict)
