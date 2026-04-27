"""顺序工作流运行器。"""

from typing import Any

from app.domain.enums import StepRunStatus
from app.runners.device_lock_manager import DeviceLockManager


class WorkflowRunner:
    """按步骤顺序执行工作流。"""

    def __init__(
        self,
        registry,
        workflow_repository,
        lock_manager: DeviceLockManager,
    ) -> None:
        """初始化工作流运行器。

        Args:
            registry: 设备注册表。
            workflow_repository: 工作流仓储。
            lock_manager: 设备锁管理器。
        """
        self._registry = registry
        self._workflow_repository = workflow_repository
        self._lock_manager = lock_manager

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
        if not self._lock_manager.acquire(device_key, run_id):
            return StepRunStatus.WAITING_DEVICE, {}

        try:
            device = self._registry.get_device(device_key)
            result = device.execute_action(
                step["action_key"],
                step.get("params", {}),
                {"run_id": run_id, "step_id": step["step_id"]},
            )
            return StepRunStatus.SUCCESS, result
        except Exception as exc:
            return StepRunStatus.FAILED, {"error": str(exc)}
        finally:
            self._lock_manager.release(device_key, run_id)
