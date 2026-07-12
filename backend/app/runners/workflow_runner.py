"""顺序工作流运行器。"""

import asyncio
import logging
from typing import Any

from app.adapters.adapter_service import AdapterService
from app.domain.adapter import ExecutionParams
from app.domain.enums import StepRunStatus
from app.domain.run_event import RunEventType
from app.runners.device_lock_manager import DeviceLockManager
from app.services.event_bus import EventBus


logger = logging.getLogger(__name__)


class WorkflowRunner:
    """按步骤顺序执行工作流。"""

    def __init__(
        self,
        lock_manager: DeviceLockManager,
        adapter_service: AdapterService,
        event_bus: EventBus | None = None,
    ) -> None:
        """初始化工作流运行器。

        Args:
            lock_manager: 设备锁管理器。
            adapter_service: 适配器服务。
            event_bus: 事件总线（可选）。
        """
        self._lock_manager = lock_manager
        self._adapter_service = adapter_service
        self._event_bus = event_bus

    def run_step(
        self,
        run_id: str,
        step: dict[str, Any],
    ) -> tuple[StepRunStatus, dict[str, Any]]:
        """执行单个工作流步骤。

        Args:
            run_id: 工作流运行标识。
            step: 工作流步骤定义。

        Returns:
            步骤执行状态与执行结果。
        """
        device_key = step["device_key"]
        action_key = step["action_key"]
        step_id = step["step_id"]

        if not self._lock_manager.acquire(device_key, run_id):
            self._emit(
                run_id,
                RunEventType.STEP_FAILED,
                step_key=step_id,
                device_id=device_key,
                message=f"设备 {device_key} 锁获取失败",
            )
            return StepRunStatus.WAITING_DEVICE, {}

        try:
            self._emit(
                run_id,
                RunEventType.STEP_STARTED,
                step_key=step_id,
                device_id=device_key,
                message=f"开始执行 {action_key}",
            )
            result = asyncio.run(self._adapter_service.execute(
                ExecutionParams(
                    run_id=run_id,
                    device_id=device_key,
                    capability_key=action_key,
                    config=step.get("params", {}),
                    confirm_params=step.get("confirm_params", {}),
                )
            ))
            if result.success:
                self._emit(
                    run_id,
                    RunEventType.STEP_COMPLETED,
                    step_key=step_id,
                    device_id=device_key,
                    payload=result.data,
                    message=f"步骤 {action_key} 执行成功",
                )
                return StepRunStatus.SUCCESS, result.data

            payload = {"error": result.error or "执行失败"}
            self._emit(
                run_id,
                RunEventType.STEP_FAILED,
                step_key=step_id,
                device_id=device_key,
                payload=payload,
                message=f"步骤 {action_key} 执行失败: {payload['error']}",
            )
            return StepRunStatus.FAILED, payload
        except Exception as exc:  # noqa: BLE001
            payload = {"error": str(exc), "error_type": exc.__class__.__name__}
            self._emit(
                run_id,
                RunEventType.STEP_FAILED,
                step_key=step_id,
                device_id=device_key,
                payload=payload,
                message=f"步骤 {action_key} 异常: {exc}",
            )
            return StepRunStatus.FAILED, payload
        finally:
            self._lock_manager.release(device_key, run_id)

    def _emit(self, run_id: str, event_type: RunEventType, **kwargs) -> None:
        """发布事件（事件总线异常不阻断主流程）。

        Args:
            run_id: 运行标识。
            event_type: 事件类型。
            **kwargs: 其他事件参数。
        """
        if self._event_bus is None:
            return
        try:
            self._event_bus.emit(run_id, event_type, **kwargs)
        except Exception:  # noqa: BLE001
            logger.warning("运行事件写入失败: %s", event_type, exc_info=True)
