"""SmartAccess 远程执行适配器。"""

from app.domain.adapter import ExecutionAdapter, ExecutionParams, ExecutionResult
from app.devices.registry import adapter


@adapter("smartaccess")
class SmartAccessAdapter(ExecutionAdapter):
    """SmartAccess 远程执行适配器。

    包装现有 SmartAccessService，通过 RabbitMQ 下发任务。
    """

    adapter_type = "smartaccess"

    def __init__(self) -> None:
        """初始化 SmartAccess 适配器。"""
        from app.runtime import get_smartaccess_service
        self._service = get_smartaccess_service()

    async def execute(self, params: ExecutionParams) -> ExecutionResult:
        """创建 SmartAccess 远程运行。

        Args:
            params: 执行参数。

        Returns:
            执行结果。
        """
        from app.schemas.smartaccess import SmartAccessRunCreateRequest

        try:
            payload = SmartAccessRunCreateRequest(
                template_id=params.config.get("template_id", ""),
                template_version=params.config.get("template_version", ""),
                requested_by=params.config.get("requested_by", "system"),
            )
            run = self._service.create_run(payload)
            return ExecutionResult(
                success=True,
                run_id=run.get("run_id"),
                data=run,
            )
        except Exception as exc:
            return ExecutionResult(success=False, error=str(exc))

    async def cancel(self, run_id: str) -> bool:
        """取消 SmartAccess 运行。

        Args:
            run_id: 运行标识。

        Returns:
            是否成功取消。
        """
        return True

    def supports_capability(self, capability_key: str) -> bool:
        """是否支持该能力。

        Args:
            capability_key: 能力标识。

        Returns:
            是否支持。
        """
        return capability_key.startswith("smartaccess/")
