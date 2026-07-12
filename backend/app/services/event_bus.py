"""事件总线。"""

from app.domain.run_event import RunEvent, RunEventType
from app.repositories.event_repository import EventRepository


class EventBus:
    """事件总线，所有状态变更通过此发布。

    借鉴 Dagster 的事件驱动模式。
    """

    def __init__(self, repo: EventRepository) -> None:
        """初始化事件总线。

        Args:
            repo: 事件仓储。
        """
        self._repo = repo

    def emit(
        self,
        run_id: str,
        event_type: RunEventType,
        payload: dict | None = None,
        message: str = "",
        step_key: str | None = None,
        device_id: str | None = None,
        adapter_type: str | None = None,
    ) -> RunEvent:
        """发布事件。

        Args:
            run_id: 运行标识。
            event_type: 事件类型。
            payload: 事件负载。
            message: 人类可读消息。
            step_key: 关联步骤。
            device_id: 设备标识。
            adapter_type: 适配器类型。

        Returns:
            已发布的事件。
        """
        event = RunEvent(
            run_id=run_id,
            event_type=event_type,
            step_key=step_key,
            device_id=device_id,
            adapter_type=adapter_type,
            payload=payload or {},
            message=message,
        )
        self._repo.store_event(event)
        return event
