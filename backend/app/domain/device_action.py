"""设备动作声明模型。"""

from typing import Any, Callable

from pydantic import BaseModel, ConfigDict, Field


class ActionSpec(BaseModel):
    """描述设备可执行动作的声明信息。"""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    action_key: str
    name: str
    description: str
    step_mode: str = "single_step"
    parameter_schema: list[dict[str, Any]] = Field(default_factory=list)
    confirm_schema: list[dict[str, Any]] = Field(default_factory=list)
    executor: Callable[..., Any]
