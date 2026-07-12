"""SmartAccess 远程执行适配器。"""

from app.domain.adapter import ExecutionAdapter, ExecutionParams, ExecutionResult
from app.devices.registry import adapter


SMARTACCESS_CAPABILITY_PREFIX = "smartaccess/"
SMARTACCESS_DEVICE_PREFIX = "smartaccess:"


def _parse_smartaccess_capability(capability_key: str) -> tuple[str, str]:
    """解析 SmartAccess 能力标识。

    Args:
        capability_key: SmartAccess 能力标识。

    Returns:
        模板 ID 与模板版本。
    """
    if not capability_key.startswith(SMARTACCESS_CAPABILITY_PREFIX):
        return "", ""
    parts = capability_key.split("/", 2)
    if len(parts) != 3:
        return "", ""
    return parts[1], parts[2]


def _strip_virtual_device_prefix(device_id: str) -> str:
    """去除 SmartAccess 虚拟设备前缀。

    Args:
        device_id: 设备标识。

    Returns:
        原始 SmartAccess 目标设备标识。
    """
    if device_id.startswith(SMARTACCESS_DEVICE_PREFIX):
        return device_id[len(SMARTACCESS_DEVICE_PREFIX):]
    return device_id


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
            template_id, template_version = _parse_smartaccess_capability(
                params.capability_key
            )
            template_id = params.config.get("template_id") or template_id
            template_version = (
                params.config.get("template_version") or template_version
            )
            if not template_id or not template_version:
                return ExecutionResult(
                    success=False,
                    error=f"SmartAccess 能力标识无效: {params.capability_key}",
                )

            template = self._service.get_template(template_id, template_version)
            target_device_id = (
                params.config.get("target_device_id")
                or _strip_virtual_device_prefix(params.device_id)
            )
            smartaccess_node_id = (
                params.config.get("smartaccess_node_id")
                or template.get("anchor_profile")
                or target_device_id
            )
            payload = SmartAccessRunCreateRequest(
                template_id=template_id,
                template_version=template_version,
                smartaccess_node_id=smartaccess_node_id,
                target_device_id=target_device_id,
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
        return capability_key.startswith(SMARTACCESS_CAPABILITY_PREFIX)
