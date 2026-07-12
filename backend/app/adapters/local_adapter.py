"""本地执行适配器。"""

from app.domain.adapter import ExecutionAdapter, ExecutionParams, ExecutionResult
from app.devices.registry import (
    adapter,
    get_capability,
    get_device,
    get_local_executor,
)


@adapter("local")
class LocalAdapter(ExecutionAdapter):
    """本地执行适配器。

    通过新注册表查找设备、能力与本地执行器。
    """

    adapter_type = "local"

    async def execute(self, params: ExecutionParams) -> ExecutionResult:
        """执行本地设备动作。

        Args:
            params: 执行参数。

        Returns:
            执行结果。
        """
        device = get_device(params.device_id)
        if not device:
            return ExecutionResult(
                success=False,
                error=f"设备 {params.device_id} 不存在",
            )

        capability = get_capability(params.capability_key)
        if not capability:
            return ExecutionResult(
                success=False,
                error=f"能力 {params.capability_key} 不存在",
            )

        try:
            executor = get_local_executor(params.device_id, params.capability_key)
            if executor is None:
                return ExecutionResult(
                    success=False,
                    error=f"设备 {params.device_id} 未注册能力 {params.capability_key} 的本地执行器",
                )
            result = executor(params.config, {"run_id": params.run_id})
            return ExecutionResult(success=True, data=result)
        except Exception as exc:
            return ExecutionResult(success=False, error=str(exc))

    async def cancel(self, run_id: str) -> bool:
        """取消运行（本地执行不支持）。

        Args:
            run_id: 运行标识。

        Returns:
            始终返回 False。
        """
        return False

    def supports_capability(self, capability_key: str) -> bool:
        """是否支持该能力。

        Args:
            capability_key: 能力标识。

        Returns:
            是否支持。
        """
        return get_capability(capability_key) is not None
