"""适配器选择服务。"""

import logging

from app.adapters.local_adapter import LocalAdapter
from app.domain.adapter import ExecutionAdapter, ExecutionParams, ExecutionResult
from app.domain.run_event import RunEventType
from app.devices.registry import get_adapter_class, get_device, list_adapter_types
from app.services.event_bus import EventBus


logger = logging.getLogger(__name__)


class AdapterService:
    """统一执行适配器选择与执行。

    替代现有分散在各处的 if/else 判断逻辑。
    """

    def __init__(self, event_bus: EventBus) -> None:
        """初始化适配器服务。

        Args:
            event_bus: 事件总线。
        """
        self._event_bus = event_bus

    def select_adapter(self, device_id: str, capability_key: str) -> ExecutionAdapter:
        """根据设备和能力选择适配器。

        Args:
            device_id: 设备标识。
            capability_key: 能力标识。

        Returns:
            选中的执行适配器。
        """
        device = get_device(device_id)

        # 1. 设备指定适配器
        if device and device.adapter_type:
            cls = get_adapter_class(device.adapter_type)
            if cls:
                return cls()

        # 2. 按能力键匹配
        for atype in list_adapter_types():
            cls = get_adapter_class(atype)
            inst = cls()
            if inst.supports_capability(capability_key):
                return inst

        # 3. 默认本地执行
        return LocalAdapter()

    async def execute(self, params: ExecutionParams) -> ExecutionResult:
        """选择适配器并执行，自动记录事件。

        Args:
            params: 执行参数。

        Returns:
            执行结果。
        """
        adapter_inst = self.select_adapter(params.device_id, params.capability_key)

        self._emit(
            params.run_id,
            RunEventType.RUNNING,
            device_id=params.device_id,
            adapter_type=adapter_inst.adapter_type,
            message=f"通过 {adapter_inst.adapter_type} 适配器执行 {params.capability_key}",
        )

        result = await adapter_inst.execute(params)

        if result.success:
            self._emit(
                params.run_id,
                RunEventType.FINISHED,
                device_id=params.device_id,
                adapter_type=adapter_inst.adapter_type,
                payload=result.data,
            )
        else:
            self._emit(
                params.run_id,
                RunEventType.FAILED,
                device_id=params.device_id,
                adapter_type=adapter_inst.adapter_type,
                payload={"error": result.error},
            )

        return result

    def _emit(self, run_id: str, event_type: RunEventType, **kwargs) -> None:
        """发布执行事件，事件写入失败不阻断执行。

        Args:
            run_id: 运行标识。
            event_type: 事件类型。
            **kwargs: 事件附加参数。
        """
        try:
            self._event_bus.emit(run_id, event_type, **kwargs)
        except Exception:  # noqa: BLE001
            logger.warning("适配器事件写入失败: %s", event_type, exc_info=True)
