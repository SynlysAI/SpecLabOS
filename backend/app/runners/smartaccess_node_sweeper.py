"""SmartAccess 执行端节点心跳超时扫描器。"""

from __future__ import annotations

import logging
from threading import Event, Thread

from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

from app.core.config import get_settings
from app.core.mongo import reset_mongo_client
from app.services.smartaccess_node_service import SmartAccessNodeService

logger = logging.getLogger(__name__)


class SmartAccessNodeSweeper:
    """周期扫描 SmartAccess 执行端心跳,将超时节点标记离线。

    心跳由执行端主动上报,扫描器仅负责把超过阈值未上报的节点从
    ``online`` 切到 ``offline``,供设备监控与远程运行入口判定可达性。
    """

    def __init__(self, service: SmartAccessNodeService) -> None:
        """初始化扫描器。

        Args:
            service: 节点心跳业务服务。
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
            name="smartaccess-node-sweeper",
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
        """按固定周期扫描失联节点。"""
        interval_seconds = max(
            get_settings().smartaccess.node_sweep_interval_seconds,
            5,
        )
        while not self._stop_event.is_set():
            try:
                count = self._service.sweep_stale_nodes()
                if count > 0:
                    logger.info("SmartAccess 心跳超时,标记 %d 个节点离线", count)
            except (ServerSelectionTimeoutError, ConnectionFailure):
                reset_mongo_client()
                logger.warning(
                    "MongoDB 连接异常,已重置客户端缓存,%ds 后重试",
                    interval_seconds,
                )
            except Exception:  # noqa: BLE001
                logger.exception(
                    "SmartAccess 节点心跳扫描异常,%ds 后重试",
                    interval_seconds,
                )
            self._stop_event.wait(interval_seconds)
