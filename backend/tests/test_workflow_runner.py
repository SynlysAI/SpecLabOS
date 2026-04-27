"""工作流运行器测试。"""

from app.domain.enums import StepRunStatus
from app.runners.device_lock_manager import DeviceLockManager
from app.runners.workflow_runner import WorkflowRunner


class FakeDevice:
    """用于测试的设备桩。"""

    def __init__(self, result=None, error: Exception | None = None) -> None:
        """初始化测试设备。"""
        self._result = result or {}
        self._error = error

    def execute_action(self, action_key: str, params: dict, context: dict) -> dict:
        """执行测试动作。"""
        if self._error is not None:
            raise self._error
        return {
            "action_key": action_key,
            "params": params,
            "context": context,
            **self._result,
        }


class FakeRegistry:
    """用于测试的注册表桩。"""

    def __init__(self, device: FakeDevice) -> None:
        """初始化测试注册表。"""
        self._device = device

    def get_device(self, device_key: str) -> FakeDevice:
        """返回测试设备。"""
        return self._device


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


def test_run_step_returns_success_when_device_action_succeeds() -> None:
    """验证运行器在设备动作成功时返回成功状态。"""
    runner = WorkflowRunner(
        registry=FakeRegistry(FakeDevice(result={"result": "ok"})),
        workflow_repository=None,
        lock_manager=DeviceLockManager(),
    )
    step = {
        "step_id": "step-1",
        "device_key": "nmr_2278",
        "action_key": "nmr.check_status",
        "params": {"sample_id": "s-1"},
    }

    status, payload = runner.run_step("run-1", step)

    assert status == StepRunStatus.SUCCESS
    assert payload["result"] == "ok"
    assert payload["context"]["run_id"] == "run-1"
    assert payload["context"]["step_id"] == "step-1"


def test_run_step_returns_failed_when_device_action_raises() -> None:
    """验证运行器在设备动作失败时返回失败状态。"""
    runner = WorkflowRunner(
        registry=FakeRegistry(FakeDevice(error=RuntimeError("device offline"))),
        workflow_repository=None,
        lock_manager=DeviceLockManager(),
    )
    step = {
        "step_id": "step-1",
        "device_key": "nmr_2278",
        "action_key": "nmr.check_status",
        "params": {},
    }

    status, payload = runner.run_step("run-1", step)

    assert status == StepRunStatus.FAILED
    assert payload == {"error": "device offline"}
