"""工作流运行器测试。"""

import pytest

from app.domain.adapter import ExecutionResult
from app.domain.enums import StepRunStatus
from app.runners.device_lock_manager import DeviceLockManager
from app.runners.workflow_runner import WorkflowRunner


class FakeAdapterService:
    """用于测试的适配器服务桩。"""

    def __init__(self, result: ExecutionResult) -> None:
        """初始化适配器服务桩。

        Args:
            result: 预设执行结果。
        """
        self._result = result
        self.params = None

    async def execute(self, params):
        """返回预设执行结果。

        Args:
            params: 执行参数。

        Returns:
            预设执行结果。
        """
        self.params = params
        return self._result


class FakeEventBus:
    """用于测试的事件总线桩。"""

    def emit(self, *args, **kwargs) -> None:
        """忽略事件写入。

        Args:
            *args: 位置参数。
            **kwargs: 关键字参数。
        """
        return None


def _build_runner(
    lock_manager: DeviceLockManager,
    result: ExecutionResult,
) -> tuple[WorkflowRunner, FakeAdapterService]:
    """构造测试运行器。

    Args:
        lock_manager: 设备锁管理器。
        result: 预设执行结果。

    Returns:
        运行器和适配器服务桩。
    """
    adapter_service = FakeAdapterService(result)
    runner = WorkflowRunner(
        lock_manager=lock_manager,
        adapter_service=adapter_service,
        event_bus=FakeEventBus(),
    )
    return runner, adapter_service


def test_same_device_cannot_be_locked_twice() -> None:
    """验证同一设备在释放前不能被第二个运行占用。"""
    manager = DeviceLockManager()

    assert manager.acquire("nmr_2278", "run-1") is True
    assert manager.acquire("nmr_2278", "run-2") is False

    manager.release("nmr_2278", "run-1")

    assert manager.acquire("nmr_2278", "run-2") is True


def test_different_devices_can_be_locked_in_parallel() -> None:
    """验证不同设备可被不同运行并发占用。"""
    manager = DeviceLockManager()

    assert manager.acquire("nmr_2278", "run-1") is True
    assert manager.acquire("gpc_2278", "run-2") is True


def test_run_step_returns_success_when_adapter_succeeds() -> None:
    """验证运行器在适配器执行成功时返回成功状态。"""
    runner, adapter_service = _build_runner(
        DeviceLockManager(),
        ExecutionResult(success=True, data={"result": "ok"}),
    )
    step = {
        "step_id": "step-1",
        "device_key": "nmr_2278",
        "action_key": "nmr.start_task",
        "params": {"sample_id": "s-1"},
    }

    status, payload = runner.run_step("run-1", step)

    assert status == StepRunStatus.SUCCESS
    assert payload["result"] == "ok"
    assert adapter_service.params.run_id == "run-1"
    assert adapter_service.params.device_id == "nmr_2278"
    assert adapter_service.params.capability_key == "nmr.start_task"


def test_run_step_returns_failed_when_adapter_fails() -> None:
    """验证运行器在适配器执行失败时返回失败状态。"""
    runner, _adapter_service = _build_runner(
        DeviceLockManager(),
        ExecutionResult(success=False, error="device offline"),
    )
    step = {
        "step_id": "step-1",
        "device_key": "nmr_2278",
        "action_key": "nmr.start_task",
        "params": {},
    }

    status, payload = runner.run_step("run-1", step)

    assert status == StepRunStatus.FAILED
    assert payload == {"error": "device offline"}


def test_run_step_returns_waiting_when_device_is_held_by_another_run() -> None:
    """验证设备被其他运行占用时返回等待状态。"""
    lock_manager = DeviceLockManager()
    runner, _adapter_service = _build_runner(
        lock_manager,
        ExecutionResult(success=True, data={"result": "ok"}),
    )
    step = {
        "step_id": "step-1",
        "device_key": "nmr_2278",
        "action_key": "nmr.start_task",
        "params": {},
    }
    lock_manager.acquire("nmr_2278", "run-1")

    status, payload = runner.run_step("run-2", step)

    assert status == StepRunStatus.WAITING_DEVICE
    assert payload == {}


def test_run_step_releases_lock_after_adapter_failure() -> None:
    """验证适配器执行失败后锁会被释放。"""
    lock_manager = DeviceLockManager()
    runner, _adapter_service = _build_runner(
        lock_manager,
        ExecutionResult(success=False, error="device offline"),
    )
    step = {
        "step_id": "step-1",
        "device_key": "nmr_2278",
        "action_key": "nmr.start_task",
        "params": {},
    }

    status, payload = runner.run_step("run-1", step)

    assert status == StepRunStatus.FAILED
    assert payload == {"error": "device offline"}
    assert lock_manager.acquire("nmr_2278", "run-2") is True


def test_run_step_does_not_swallow_programming_errors() -> None:
    """验证明显的程序错误不会被静默转成失败状态。"""
    runner, _adapter_service = _build_runner(
        DeviceLockManager(),
        ExecutionResult(success=True, data={"result": "ok"}),
    )
    step = {
        "device_key": "nmr_2278",
        "action_key": "nmr.start_task",
        "params": {},
    }

    with pytest.raises(KeyError):
        runner.run_step("run-1", step)
