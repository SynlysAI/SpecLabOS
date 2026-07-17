"""SmartAccess 运行超时扫描器。"""

from __future__ import annotations

import logging
from threading import Event, Thread

from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

from app.core.config import get_settings
from app.core.mongo import reset_mongo_client
from app.services.smartaccess_service import SmartAccessService

logger = logging.getLogger(__name__)


class SmartAccessRunSweeper:
    """周期扫描 SmartAccess 运行，将超时任务标记失败。

    负责两类超时：
    1. queued 状态超过 queued_timeout_seconds 未被消费，判定执行端失联。
    2. running 状态单步超过 step_timeout_seconds 无事件更新，判定执行端卡死。

    实际状态推进委托给 SmartAccessService.sweep_stale_runs，
    通过追加 run.failed 事件走既有状态机，前端无需改动。
    """

    def __init__(self, service: SmartAccessService) -> None:
        """初始化扫描器。

        Args:
            service: SmartAccess 业务服务。
        """
        self._service = service
        self._stop_event = Event()
        self._thread: Thread | None = None

    def start(self) -> None:
        """启动后台扫描线程。"""
        if self._thread is not None and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = Thread(
            target=self._sweep_loop,
            name="smartaccess-run-sweeper",
            daemon=True,
        )
        self._thread.start()

    def stop(self) -> None:
        """停止后台扫描线程。"""
        self._stop_event.set()
        thread = self._thread
        self._thread = None
        if thread is not None and thread.is_alive():
            thread.join(timeout=2)

    def _sweep_loop(self) -> None:
        """按固定周期扫描超时运行。"""
        interval_seconds = max(
            get_settings().smartaccess.sweep_interval_seconds,
            5,
        )
        while not self._stop_event.is_set():
            try:
                self._service.sweep_stale_runs()
            except (ServerSelectionTimeoutError, ConnectionFailure):
                reset_mongo_client()
                logger.warning(
                    "MongoDB 连接异常，已重置客户端缓存，%ds 后重试",
                    interval_seconds,
                )
            except Exception:  # noqa: BLE001
                logger.exception(
                    "SmartAccess 超时扫描异常，%ds 后重试",
                    interval_seconds,
                )
            self._stop_event.wait(interval_seconds)
