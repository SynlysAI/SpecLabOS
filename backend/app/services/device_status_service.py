"""设备状态探测服务。"""

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime
import socket
from typing import Any
from urllib.parse import urlparse
from uuid import uuid4

import requests
from requests import exceptions as request_exceptions

from app.core.config import get_settings
from app.devices.registry import get_local_executor
from app.domain.device import DeviceResource


DEFAULT_STATUS_TIMEOUT_SECONDS = 1


@dataclass(frozen=True)
class StatusProbeSpec:
    """设备状态探测配置。"""

    capability_key: str
    params: dict[str, Any] = field(default_factory=dict)
    source: str = "status_api"
    timeout_seconds: float = DEFAULT_STATUS_TIMEOUT_SECONDS


STATUS_PROBE_SPECS: dict[str, StatusProbeSpec] = {
    "nmr_2278": StatusProbeSpec("nmr.list_templates", source="nmr_check"),
    "gpc_2278": StatusProbeSpec("gpc.get_device_status_detail"),
    "pi_2278": StatusProbeSpec("pi.health_check", source="health_api"),
    "metal_108": StatusProbeSpec("metal_108.health_check", source="health_api"),
    "cat_108": StatusProbeSpec("cat_108.health_check", source="health_api"),
    "micro_108": StatusProbeSpec("micro_108.health_check", source="health_api"),
}

TCP_PROBE_DEVICE_IDS = {
    "nmr_2278",
    "gpc_2278",
    "ir_2278",
    "raman_2278",
    "lcms_2278",
    "resin_2278",
    "resin_2278_2",
    "resin_1438",
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
        max_workers = min(len(devices), 16)
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
        if not device.enabled:
            self._mark_disabled(device)
            return device
        if device.adapter_type == "smartaccess":
            return device
        if self._has_config_probe(device.device_id):
            self._refresh_by_config_probe(device)
            return device
        if device.device_id in TCP_PROBE_DEVICE_IDS:
            self._refresh_by_tcp_probe(device)
            return device
        if spec is None:
            self._mark_unknown(device, "未配置状态探测接口")
            return device

        executor = get_local_executor(device.device_id, spec.capability_key)
        if executor is None:
            self._mark_unknown(device, f"未注册状态执行器: {spec.capability_key}")
            return device

        try:
            result = executor(
                self._build_probe_params(spec),
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
    def _has_config_probe(device_id: str) -> bool:
        """判断设备是否配置了实例级状态探测。"""
        item_config = get_settings().devices.items.get(device_id)
        return bool(item_config and item_config.endpoints)

    @staticmethod
    def _refresh_by_config_probe(device: DeviceResource) -> None:
        """按设备实例配置刷新状态。

        Args:
            device: 待刷新设备。
        """
        item_config = get_settings().devices.items.get(device.device_id)
        if item_config is None:
            DeviceStatusService._mark_unknown(device, "未配置设备实例")
            return

        spec = StatusProbeSpec(
            "config_probe",
            source="device_config",
            timeout_seconds=(
                item_config.status_timeout_seconds
                or DEFAULT_STATUS_TIMEOUT_SECONDS
            ),
        )
        if item_config.health_path:
            DeviceStatusService._refresh_by_config_health_probe(
                device,
                item_config.endpoints,
                item_config.health_path,
                item_config.health_device,
                spec,
            )
            return

        urls = DeviceStatusService._resolve_config_status_urls(
            item_config.endpoints,
            item_config.status_endpoints,
        )
        if not urls:
            DeviceStatusService._mark_unknown(device, "未配置状态探测地址")
            return
        DeviceStatusService._refresh_by_tcp_urls(device, urls, spec)

    @staticmethod
    def _refresh_by_config_health_probe(
        device: DeviceResource,
        endpoints: dict[str, str],
        health_path: str,
        health_device: str,
        spec: StatusProbeSpec,
    ) -> None:
        """按配置请求健康检查接口。

        Args:
            device: 待刷新设备。
            endpoints: 设备端点映射。
            health_path: 健康检查路径。
            health_device: 健康检查设备标识。
            spec: 状态探测配置。
        """
        base_url = endpoints.get("api") or next(iter(endpoints.values()), "")
        if not base_url:
            DeviceStatusService._mark_unknown(device, "未配置健康检查地址")
            return
        try:
            response = requests.get(
                f"{base_url.rstrip('/')}/{health_path.lstrip('/')}",
                timeout=spec.timeout_seconds,
            )
            response.raise_for_status()
            result = response.json()
        except request_exceptions.Timeout as exc:
            DeviceStatusService._mark_offline(device, f"健康检查超时: {exc}", spec)
            return
        except request_exceptions.ConnectionError as exc:
            DeviceStatusService._mark_offline(device, f"健康检查连接失败: {exc}", spec)
            return
        except request_exceptions.HTTPError as exc:
            DeviceStatusService._mark_http_error(device, exc, spec)
            return
        except request_exceptions.RequestException as exc:
            DeviceStatusService._mark_error(device, f"健康检查请求失败: {exc}", spec)
            return
        except ValueError as exc:
            DeviceStatusService._mark_error(device, f"健康检查响应不是 JSON: {exc}", spec)
            return

        loaded_devices = result.get("devices_loaded", [])
        if health_device and health_device not in loaded_devices:
            DeviceStatusService._mark_error(
                device,
                f"健康检查未加载设备: {health_device}",
                spec,
            )
            return
        DeviceStatusService._mark_connected(
            device,
            {**result, "device_status": "idle"},
            spec,
        )

    @staticmethod
    def _resolve_config_status_urls(
        endpoints: dict[str, str],
        status_endpoints: list[str],
    ) -> list[str]:
        """解析配置中用于状态探测的端点地址。

        Args:
            endpoints: 设备端点映射。
            status_endpoints: 状态探测端点名称列表。

        Returns:
            状态探测 URL 列表。
        """
        if not status_endpoints:
            return [url for url in endpoints.values() if url]
        return [endpoints[name] for name in status_endpoints if endpoints.get(name)]

    @staticmethod
    def _refresh_by_tcp_probe(device: DeviceResource) -> None:
        """通过服务端口可达性刷新设备状态。

        Args:
            device: 待刷新设备。
        """
        timeout_seconds = DEFAULT_STATUS_TIMEOUT_SECONDS
        urls = DeviceStatusService._build_tcp_probe_urls(device.device_id)
        if not urls:
            DeviceStatusService._mark_unknown(device, "未配置端口探测地址")
            return
        spec = StatusProbeSpec(
            capability_key="tcp.port_check",
            source="tcp_probe",
            timeout_seconds=timeout_seconds,
        )
        DeviceStatusService._refresh_by_tcp_urls(device, urls, spec)

    @staticmethod
    def _refresh_by_tcp_urls(
        device: DeviceResource,
        urls: list[str],
        spec: StatusProbeSpec,
    ) -> None:
        """按指定 URL 列表执行 TCP 探测。

        Args:
            device: 待刷新设备。
            urls: 状态探测 URL 列表。
            spec: 状态探测配置。
        """
        reachable_urls, failed_urls = DeviceStatusService._probe_tcp_urls(
            urls,
            spec.timeout_seconds,
        )
        if reachable_urls:
            result = {
                "status": "idle",
                "reachable_urls": reachable_urls,
                "failed_urls": failed_urls,
            }
            DeviceStatusService._mark_connected(device, result, spec)
            device.status_message = DeviceStatusService._build_tcp_success_message(
                reachable_urls,
                failed_urls,
            )
            return

        DeviceStatusService._mark_offline(
            device,
            f"服务端口不可达: {', '.join(failed_urls or urls)}",
            spec,
        )

    @staticmethod
    def _build_probe_params(spec: StatusProbeSpec) -> dict[str, Any]:
        """构建设备状态探测参数。

        Args:
            spec: 状态探测配置。

        Returns:
            带短超时的状态探测参数。
        """
        params = dict(spec.params)
        params.setdefault("timeout", spec.timeout_seconds)
        return params

    @staticmethod
    def _build_tcp_probe_urls(device_id: str) -> list[str]:
        """构建设备端口探测地址。

        Args:
            device_id: 设备标识。

        Returns:
            该设备需要探测的基础服务地址列表。
        """
        settings = get_settings()
        if device_id == "nmr_2278":
            return [settings.apis.nmr.base_url] if settings.apis.nmr.base_url else []
        if device_id == "gpc_2278":
            return [settings.apis.gpc.base_url] if settings.apis.gpc.base_url else []
        if device_id == "pi_2278":
            return [settings.apis.pi.base_url] if settings.apis.pi.base_url else []
        if device_id == "lcms_2278":
            return [settings.apis.lcms.base_url] if settings.apis.lcms.base_url else []
        if device_id == "raman_2278":
            return [
                url for url in (
                    settings.apis.raman.capture_base_url,
                    settings.apis.raman.result_base_url,
                )
                if url
            ]
        if device_id.startswith("resin_"):
            base_url = (
                settings.apis.resin.devices.get(device_id)
                or settings.apis.resin.base_url
            )
            return [base_url] if base_url else []
        return []

    @staticmethod
    def _probe_tcp_urls(
        urls: list[str],
        timeout_seconds: float,
    ) -> tuple[list[str], list[str]]:
        """探测多个服务地址的 TCP 端口可达性。

        Args:
            urls: 服务基础地址列表。
            timeout_seconds: 单个端口连接超时时间。

        Returns:
            可达地址列表与不可达地址列表。
        """
        reachable_urls = []
        failed_urls = []
        with ThreadPoolExecutor(max_workers=min(len(urls), 8) or 1) as executor:
            future_map = {
                executor.submit(
                    DeviceStatusService._is_tcp_url_reachable,
                    url,
                    timeout_seconds,
                ): url
                for url in urls
            }
            for future in as_completed(future_map):
                url = future_map[future]
                if future.result():
                    reachable_urls.append(url)
                else:
                    failed_urls.append(url)
        return reachable_urls, failed_urls

    @staticmethod
    def _is_tcp_url_reachable(url: str, timeout_seconds: float) -> bool:
        """判断服务地址的 TCP 端口是否可连接。

        Args:
            url: 服务基础地址。
            timeout_seconds: 连接超时时间。

        Returns:
            端口可连接时返回 True。
        """
        parsed_url = urlparse(url if "://" in url else f"http://{url}")
        host = parsed_url.hostname
        port = parsed_url.port
        if port is None:
            port = 443 if parsed_url.scheme == "https" else 80
        if not host:
            return False
        try:
            with socket.create_connection((host, port), timeout=timeout_seconds):
                return True
        except OSError:
            return False

    @staticmethod
    def _build_tcp_success_message(
        reachable_urls: list[str],
        failed_urls: list[str],
    ) -> str:
        """构造端口探测成功消息。

        Args:
            reachable_urls: 可达地址列表。
            failed_urls: 不可达地址列表。

        Returns:
            前端展示的状态消息。
        """
        message = f"服务端口可达: {', '.join(reachable_urls)}"
        if failed_urls:
            message = f"{message}；不可达: {', '.join(failed_urls)}"
        return message

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
    def _mark_disabled(device: DeviceResource) -> None:
        """标记设备未启用。"""
        device.connection_status = "disabled"
        device.execution_status = "idle"
        device.data_status = "unknown"
        device.maintenance_status = "available"
        device.status_sources = []
        device.status_message = "设备已禁用，跳过状态探测"

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
