"""SmartAccess 执行端节点心跳业务服务。"""

from datetime import datetime, timezone
from typing import Any

from app.core.config import get_settings
from app.core.datetime_utils import format_datetime
from app.repositories.smartaccess_node_repository import (
    SmartAccessNodeRepository,
)


def _seconds_since(value: Any) -> float | None:
    """计算给定时间距现在的秒数。

    Args:
        value: 时间值,期望为 datetime。

    Returns:
        距现在的秒数;入参非 datetime 时返回 None。
    """
    if not isinstance(value, datetime):
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return max(0.0, (datetime.now(timezone.utc) - value).total_seconds())


def _format_dt(value: Any) -> str:
    """格式化时间字段为展示文本。

    Args:
        value: 原始时间值。

    Returns:
        格式化后的文本,无值时返回 "--"。
    """
    if not isinstance(value, datetime):
        return "--"
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return format_datetime(value)


class SmartAccessNodeService:
    """SmartAccess 执行端节点心跳与在线状态服务。"""

    def __init__(self, repository: SmartAccessNodeRepository) -> None:
        """初始化服务。

        Args:
            repository: 节点心跳仓储。
        """
        self._repository = repository

    def receive_heartbeat(
        self,
        node_id: str,
        *,
        device_info: dict[str, Any] | None = None,
        heartbeat_interval_seconds: int | None = None,
    ) -> dict:
        """接收一次心跳并更新节点状态。

        Args:
            node_id: 执行端节点标识。
            device_info: 执行端上报的设备元信息。
            heartbeat_interval_seconds: 执行端上报周期。

        Returns:
            更新后的节点文档。
        """
        if not node_id:
            raise ValueError("node_id 不能为空")
        return self._repository.upsert_heartbeat(
            node_id,
            device_info=device_info,
            heartbeat_interval_seconds=heartbeat_interval_seconds,
        )

    def register_node(
        self,
        node_id: str,
        *,
        machine_fingerprint: str,
        device_info: dict[str, Any] | None = None,
    ) -> dict:
        """注册并校验 SmartAccess 执行端节点身份。

        Args:
            node_id: 执行端节点标识。
            machine_fingerprint: 本机指纹。
            device_info: 执行端上报的设备元信息。

        Returns:
            注册结果，包含是否冲突。
        """

        if not node_id:
            raise ValueError("node_id 不能为空")
        if not machine_fingerprint:
            raise ValueError("machine_fingerprint 不能为空")
        result = self._repository.register_node(
            node_id,
            machine_fingerprint=machine_fingerprint,
            device_info=device_info,
        )
        node = result.get("node") or {}
        return {
            "ok": bool(result.get("ok")),
            "conflict": bool(result.get("conflict")),
            "node_id": node_id,
            "existing_machine_fingerprint": str(
                node.get("machine_fingerprint") or ""
            ),
            "existing_device_info": node.get("device_info") or {},
            "status": node.get("status", "registered"),
        }

    def list_nodes(self) -> list[dict]:
        """列出全部节点并附带距上次心跳的秒数。

        Returns:
            节点展示对象列表。
        """
        records = self._repository.list_nodes()
        return [self._to_view(item) for item in records]

    def get_node_status(self, node_id: str) -> str | None:
        """查询指定节点的在线状态。

        Args:
            node_id: 执行端节点标识。

        Returns:
            节点状态文本;节点不存在时返回 None。
        """
        record = self._repository.find_node(node_id)
        if not record:
            return None
        return record.get("status", "offline")

    def sweep_stale_nodes(self) -> int:
        """扫描超过阈值未上报心跳的节点,标记为离线。

        Returns:
            本次被标记离线的节点数量。
        """
        threshold = get_settings().smartaccess.node_offline_threshold_seconds
        stale = self._repository.list_stale_nodes(threshold)
        for record in stale:
            self._repository.mark_offline(record["node_id"])
        return len(stale)

    @staticmethod
    def _to_view(record: dict) -> dict:
        """将节点文档转换为展示对象。

        Args:
            record: 节点仓储文档。

        Returns:
            展示视图字典。
        """
        return {
            "node_id": record.get("node_id", ""),
            "status": record.get("status", "offline"),
            "last_heartbeat_at": _format_dt(record.get("last_heartbeat_at")),
            "first_seen_at": _format_dt(record.get("first_seen_at")),
            "seconds_since_heartbeat": _seconds_since(
                record.get("last_heartbeat_at")
            ),
            "heartbeat_interval_seconds": int(
                record.get("heartbeat_interval_seconds") or 30
            ),
            "machine_fingerprint": record.get("machine_fingerprint") or "",
            "device_info": record.get("device_info") or {},
        }
