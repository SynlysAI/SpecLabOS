"""工作流后台调度器。"""

from __future__ import annotations

from threading import Event, Lock, Thread
from traceback import format_exc

from app.core.config import get_settings
from app.domain.enums import StepRunStatus, WorkflowRunStatus


class WorkflowDispatcher:
    """按设备串行调度工作流运行。"""

    def __init__(self, workflow_repository, workflow_runner, lock_manager) -> None:
        """初始化工作流调度器。

        Args:
            workflow_repository: 工作流运行记录仓储。
            workflow_runner: 单步工作流运行器。
            lock_manager: 设备锁管理器。
        """
        self._workflow_repository = workflow_repository
        self._workflow_runner = workflow_runner
        self._lock_manager = lock_manager
        self._stop_event = Event()
        self._guard = Lock()
        self._thread: Thread | None = None
        self._active_runs: set[str] = set()

    def start(self) -> None:
        """启动后台调度线程。"""
        with self._guard:
            if self._thread is not None and self._thread.is_alive():
                return
            self._stop_event.clear()
            self._thread = Thread(
                target=self._dispatch_loop,
                name="workflow-dispatcher",
                daemon=True,
            )
            self._thread.start()

    def stop(self) -> None:
        """停止后台调度线程。"""
        self._stop_event.set()
        with self._guard:
            thread = self._thread
            self._thread = None
        if thread is not None and thread.is_alive():
            thread.join(timeout=2)

    def _dispatch_loop(self) -> None:
        """按固定周期扫描待执行工作流。"""
        interval_seconds = max(get_settings().runtime.runner_interval_seconds, 1)
        while not self._stop_event.is_set():
            self._dispatch_once()
            self._stop_event.wait(interval_seconds)

    def _dispatch_once(self) -> None:
        """扫描并启动可执行工作流。"""
        for run in self._workflow_repository.list_runs_by_status(
            [WorkflowRunStatus.QUEUED.value]
        ):
            run_id = run["run_id"]
            with self._guard:
                if run_id in self._active_runs:
                    continue
                self._active_runs.add(run_id)
            Thread(
                target=self._execute_run,
                args=(run_id,),
                name=f"workflow-run-{run_id}",
                daemon=True,
            ).start()

    def _execute_run(self, run_id: str) -> None:
        """执行单个工作流的全部步骤。

        Args:
            run_id: 工作流运行标识。
        """
        device_key = ""
        try:
            run = self._workflow_repository.get_run(run_id)
            if run is None:
                return

            step_runs = run.get("step_runs", [])
            if not step_runs:
                self._workflow_repository.mark_run_success(run_id)
                return

            device_key = step_runs[0]["device_key"]
            if not self._lock_manager.acquire(device_key, run_id):
                self._workflow_repository.mark_run_queued(run_id)
                return

            self._workflow_repository.mark_run_started(run_id)
            total_steps = len(step_runs)
            for index, step in enumerate(step_runs):
                self._workflow_repository.mark_step_running(
                    run_id=run_id,
                    step_index=index,
                    current_step_index=index + 1,
                )
                status, payload = self._workflow_runner.run_step(run_id, step)
                if status == StepRunStatus.SUCCESS:
                    self._workflow_repository.mark_step_success(
                        run_id=run_id,
                        step_index=index,
                        payload=payload,
                    )
                    continue

                if status == StepRunStatus.WAITING_DEVICE:
                    self._workflow_repository.mark_step_pending(run_id, index)
                    self._workflow_repository.mark_run_queued(run_id)
                    return

                self._workflow_repository.mark_step_failed(
                    run_id=run_id,
                    step_index=index,
                    payload=payload,
                )
                self._workflow_repository.mark_run_failed(run_id, payload)
                return

            self._workflow_repository.mark_run_success(
                run_id=run_id,
                summary={"completed_steps": total_steps},
            )
        except Exception as exc:  # noqa: BLE001
            self._workflow_repository.mark_run_failed(
                run_id=run_id,
                summary={
                    "error": str(exc),
                    "error_type": exc.__class__.__name__,
                    "traceback": format_exc(),
                },
            )
        finally:
            if device_key:
                self._lock_manager.release(device_key, run_id)
            with self._guard:
                self._active_runs.discard(run_id)
