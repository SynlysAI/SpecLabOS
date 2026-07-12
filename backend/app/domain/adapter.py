"""执行适配器抽象基类。"""

from abc import ABC, abstractmethod

from pydantic import BaseModel, Field


class ExecutionParams(BaseModel):
    """执行参数。"""

    run_id: str
    device_id: str
    capability_key: str
    config: dict = Field(default_factory=dict)
    confirm_params: dict = Field(default_factory=dict)


class ExecutionResult(BaseModel):
    """执行结果。"""

    success: bool
    run_id: str | None = None
    data: dict = Field(default_factory=dict)
    error: str | None = None


class ExecutionAdapter(ABC):
    """执行适配器抽象基类。

    借鉴 Dagster Executor 模式。每种执行通道（本地、SmartAccess、FastAPI、SDK）
    实现一个 Adapter，由 AdapterService 根据设备和能力选择。
    """

    adapter_type: str

    @abstractmethod
    async def execute(self, params: ExecutionParams) -> ExecutionResult:
        """执行实验任务。"""
        ...

    @abstractmethod
    async def cancel(self, run_id: str) -> bool:
        """取消运行。"""
        ...

    @abstractmethod
    def supports_capability(self, capability_key: str) -> bool:
        """是否支持该能力。"""
        ...
