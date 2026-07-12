"""设备状态探测服务。"""

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import uuid4

from requests import exceptions as request_exceptions

from app.devices.registry import get_local_executor
from app.domain.device import DeviceResource


@dataclass(frozen=True)
class StatusProbeSpec:
    """设备状态探测配置。"""

    capability_key: str
    params: dict[str, Any] = field(default_factory=dict)
    source: str = "status_api"


STATUS_PROBE_SPECS: dict[str, StatusProbeSpec] = {
    "nmr_2278": StatusProbeSpec("nmr.list_templates", source="nmr_check"),
    "gpc_2278": StatusProbeSpec("gpc.get_device_status_detail"),
    "pi_2278": StatusProbeSpec("pi.health_check", source="health_api"),
    "resin_2278": StatusProbeSpec("resin.health_check", source="health_api"),
    "resin_2278_2": StatusProbeSpec("resin.health_check", source="health_api"),
    "resin_1438": StatusProbeSpec("resin.health_check", source="health_api"),
    "metal_108": StatusProbeSpec("metal_108.check_status"),
    "cat_108": StatusProbeSpec("cat_108.check_status"),
    "micro_108": StatusProbeSpec("micro_108.check_status"),
}


class DeviceStatusService:
    """通过设备状态接口刷新四维状态。"""

    def refresh_devices(self, devices: list[DeviceResource]) -> list[DeviceResource]:
        """并发刷新设备状态。

        Args:
            devices: 待刷新设备列表。

        Returns:
            刷新后的设备列表。
        """
        if not devices:
            return devices
        max_workers = min(len(devices), 8)
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_map = {
                executor.submit(self.refresh_device, device): device
                for device in devices
            }
            for future in as_completed(future_map):
                future.result()
        return devices

    def refresh_device(self, device: DeviceResource) -> DeviceResource:
        """刷新单台设备状态。

        Args:
            device: 待刷新设备。

        Returns:
            刷新后的设备。
        """
        spec = STATUS_PROBE_SPECS.get(device.device_id)
        device.status_updated_at = datetime.now()
        if spec is None:
            self._mark_unknown(device, "未配置状态探测接口")
            return device

        executor = get_local_executor(device.device_id, spec.capability_key)
        if executor is None:
            self._mark_unknown(device, f"未注册状态执行器: {spec.capability_key}")
            return device

        try:
            result = executor(
                spec.params,
                {"run_id": f"status-{uuid4()}", "source": "status_probe"},
            )
        except request_exceptions.Timeout as exc:
            self._mark_offline(device, f"状态接口超时: {exc}", spec)
            return device
        except request_exceptions.ConnectionError as exc:
            self._mark_offline(device, f"状态接口连接失败: {exc}", spec)
            return device
        except request_exceptions.HTTPError as exc:
            self._mark_http_error(device, exc, spec)
            return device
        except request_exceptions.RequestException as exc:
            self._mark_error(device, f"状态接口请求失败: {exc}", spec)
            return device
        except Exception as exc:  # noqa: BLE001
            self._mark_error(device, f"状态探测异常: {exc}", spec)
            return device

        self._mark_connected(device, result, spec)
        return device

    @staticmethod
    def _mark_connected(
        device: DeviceResource,
        result: dict[str, Any],
        spec: StatusProbeSpec,
    ) -> None:
        """标记设备连接成功。

        Args:
            device: 设备资源。
            result: 状态接口返回。
            spec: 状态探测配置。
        """
        device.connection_status = "online"
        device.execution_status = DeviceStatusService._extract_execution_status(result)
        device.data_status = "available"
        device.maintenance_status = "available"
        device.status_sources = [spec.source, spec.capability_key]
        device.status_message = DeviceStatusService._build_success_message(result)

    @staticmethod
    def _mark_unknown(device: DeviceResource, message: str) -> None:
        """标记设备状态未知。

        Args:
            device: 设备资源。
            message: 状态消息。
        """
        device.connection_status = "unknown"
        device.execution_status = "idle"
        device.data_status = "unknown"
        device.maintenance_status = "available"
        device.status_sources = []
        device.status_message = message

    @staticmethod
    def _mark_offline(
        device: DeviceResource,
        message: str,
        spec: StatusProbeSpec,
    ) -> None:
        """标记设备离线。

        Args:
            device: 设备资源。
            message: 状态消息。
            spec: 状态探测配置。
        """
        device.connection_status = "offline"
        device.execution_status = "idle"
        device.data_status = "unknown"
        device.maintenance_status = "available"
        device.status_sources = [spec.source, spec.capability_key]
        device.status_message = message

    @staticmethod
    def _mark_http_error(
        device: DeviceResource,
        exc: request_exceptions.HTTPError,
        spec: StatusProbeSpec,
    ) -> None:
        """按 HTTP 状态标记设备错误。

        Args:
            device: 设备资源。
            exc: HTTP 异常。
            spec: 状态探测配置。
        """
        status_code = exc.response.status_code if exc.response is not None else 0
        if status_code >= 500:
            device.connection_status = "offline"
            device.execution_status = "idle"
            device.status_message = f"设备离线或状态服务不可用: HTTP {status_code}"
        else:
            device.connection_status = "online"
            device.execution_status = "error"
            device.status_message = f"状态接口 HTTP 错误 {status_code}: {exc}"
        device.data_status = "unknown"
        device.maintenance_status = "available"
        device.status_sources = [spec.source, spec.capability_key]

    @staticmethod
    def _mark_error(
        device: DeviceResource,
        message: str,
        spec: StatusProbeSpec,
    ) -> None:
        """标记设备状态错误。

        Args:
            device: 设备资源。
            message: 状态消息。
            spec: 状态探测配置。
        """
        device.connection_status = "error"
        device.execution_status = "error"
        device.data_status = "unknown"
        device.maintenance_status = "available"
        device.status_sources = [spec.source, spec.capability_key]
        device.status_message = message

    @staticmethod
    def _extract_execution_status(result: dict[str, Any]) -> str:
        """从设备返回中提取执行状态。

        Args:
            result: 状态接口返回。

        Returns:
            标准执行状态。
        """
        raw_status = DeviceStatusService._find_status_value(result)
        normalized = str(raw_status or "").lower()
        if normalized in {"running", "busy", "processing", "in_progress", "执行中"}:
            return "running"
        if normalized in {"error", "failed", "failure", "异常", "故障"}:
            return "error"
        if normalized in {"warning", "warn", "告警"}:
            return "warning"
        return "idle"

    @staticmethod
    def _find_status_value(payload: Any) -> Any:
        """递归查找状态字段。

        Args:
            payload: 状态接口返回。

        Returns:
            状态字段值，不存在时返回 None。
        """
        if isinstance(payload, dict):
            for key in ("execution_status", "device_status", "status", "state"):
                if key in payload:
                    return payload[key]
            for value in payload.values():
                found = DeviceStatusService._find_status_value(value)
                if found is not None:
                    return found
        if isinstance(payload, list):
            for item in payload:
                found = DeviceStatusService._find_status_value(item)
                if found is not None:
                    return found
        return None

    @staticmethod
    def _build_success_message(result: dict[str, Any]) -> str:
        """构造状态成功消息。

        Args:
            result: 状态接口返回。

        Returns:
            状态消息。
        """
        if not result:
            return "状态接口已响应"
        status = DeviceStatusService._find_status_value(result)
        if status is not None:
            return f"状态接口已响应，状态: {status}"
        return "状态接口已响应"
