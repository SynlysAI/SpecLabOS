"""树脂处理设备定义。"""

from typing import Any

import requests

from app.core.config import get_settings
from app.devices.registry import capability, device, local_executor
from app.domain.capability import DeviceCapability
from app.domain.device import DeviceResource


@device
class ResinDeviceDefault(DeviceResource):
    """Resin 树脂工作站（默认实例）。"""

    device_id: str = "resin_2278"
    name: str = "resin_2278"
    category: str = "树脂工作站"
    device_type: str = "ResinWorkstation"
    location: str = "B-201"


@device
class ResinDevice2(DeviceResource):
    """Resin 树脂工作站（第二实例）。"""

    device_id: str = "resin_2278_2"
    name: str = "resin_2278_2"
    category: str = "树脂工作站"
    device_type: str = "ResinWorkstation"
    location: str = "B-202"


@device
class ResinDevice3(DeviceResource):
    """Resin 树脂工作站（第三实例）。"""

    device_id: str = "resin_1438"
    name: str = "resin_1438"
    category: str = "树脂工作站"
    device_type: str = "ResinWorkstation"
    location: str = "B-203"


for _resin_device_id in ("resin_2278", "resin_2278_2", "resin_1438"):

    @local_executor(_resin_device_id, "resin.health_check")
    def resin_health_check_executor(
        params: dict[str, Any],
        context: dict[str, Any],
        device_id: str = _resin_device_id,
    ) -> dict[str, Any]:
        """执行 Resin 健康检查。

        Args:
            params: 执行参数。
            context: 运行上下文。
            device_id: 设备标识。

        Returns:
            Resin 服务响应。
        """
        return _request_resin(device_id, "GET", "/health", timeout=params.get("timeout"))

    @local_executor(_resin_device_id, "resin.trigger_generate")
    def resin_trigger_generate_executor(
        params: dict[str, Any],
        context: dict[str, Any],
        device_id: str = _resin_device_id,
    ) -> dict[str, Any]:
        """触发 Resin 解析实验方案。

        Args:
            params: 执行参数。
            context: 运行上下文。
            device_id: 设备标识。

        Returns:
            Resin 服务响应。
        """
        payload = {"experiment_plan": params.get("experiment_plan", "")}
        if params.get("request_id"):
            payload["request_id"] = params["request_id"]
        return _request_resin(
            device_id,
            "POST",
            "/api/v1/experiment/trigger",
            payload,
        )

    @local_executor(_resin_device_id, "resin.execute_process")
    def resin_execute_process_executor(
        params: dict[str, Any],
        context: dict[str, Any],
        device_id: str = _resin_device_id,
    ) -> dict[str, Any]:
        """执行 Resin 工艺流程。

        Args:
            params: 执行参数。
            context: 运行上下文。
            device_id: 设备标识。

        Returns:
            Resin 服务响应。
        """
        payload = {"request_id": params["request_id"]} if params.get("request_id") else None
        return _request_resin(
            device_id,
            "POST",
            "/api/v1/experiment/execute",
            payload,
        )

    @local_executor(_resin_device_id, "resin.get_experiment_status")
    def resin_get_experiment_status_executor(
        params: dict[str, Any],
        context: dict[str, Any],
        device_id: str = _resin_device_id,
    ) -> dict[str, Any]:
        """查询 Resin 流程执行状态。

        Args:
            params: 执行参数。
            context: 运行上下文。
            device_id: 设备标识。

        Returns:
            Resin 服务响应。
        """
        return _request_resin(device_id, "GET", "/api/v1/experiment/status")


@capability("树脂工作站")
def resin_health_check() -> DeviceCapability:
    """健康检查。"""
    return DeviceCapability(
        capability_key="resin.health_check",
        device_category="树脂工作站",
        name="健康检查",
        description="检查 Resin 工作站健康状态",
        step_mode="auto",
    )


@capability("树脂工作站")
def resin_trigger_generate() -> DeviceCapability:
    """触发解析。"""
    return DeviceCapability(
        capability_key="resin.trigger_generate",
        device_category="树脂工作站",
        name="触发解析",
        description="触发 Resin 解析实验方案",
        step_mode="auto",
        parameter_schema={
            "type": "object",
            "properties": {
                "experiment_plan": {"type": "string", "description": "实验方案文本"},
                "request_id": {"type": "string", "description": "可选请求标识"},
            },
            "required": ["experiment_plan"],
        },
    )


@capability("树脂工作站")
def resin_execute_process() -> DeviceCapability:
    """执行流程。"""
    return DeviceCapability(
        capability_key="resin.execute_process",
        device_category="树脂工作站",
        name="执行流程",
        description="执行 Resin 工艺流程",
        step_mode="auto",
        parameter_schema={
            "type": "object",
            "properties": {
                "request_id": {"type": "string", "description": "可选请求标识"},
            },
        },
    )


@capability("树脂工作站")
def resin_get_experiment_status() -> DeviceCapability:
    """查询流程状态。"""
    return DeviceCapability(
        capability_key="resin.get_experiment_status",
        device_category="树脂工作站",
        name="查询流程状态",
        description="查询 Resin 流程执行状态",
        step_mode="auto",
    )


def _request_resin(
    device_id: str,
    method: str,
    path: str,
    payload: dict[str, Any] | None = None,
    timeout: float | None = None,
) -> dict[str, Any]:
    """调用 Resin 远程接口。

    Args:
        device_id: 设备标识。
        method: HTTP 方法。
        path: 接口路径。
        payload: 请求体。
        timeout: 请求超时时间。

    Returns:
        Resin 服务响应。
    """
    settings = get_settings()
    item_config = settings.devices.items.get(device_id)
    base_url = (
        item_config.endpoints.get("api") if item_config is not None else None
    ) or (
        settings.apis.resin.devices.get(device_id)
        or settings.apis.resin.base_url
    ).rstrip("/")
    response = requests.request(
        method=method,
        url=f"{base_url}{path}",
        timeout=timeout or settings.apis.resin.timeout,
        json=payload,
    )
    response.raise_for_status()
    try:
        return response.json()
    except ValueError:
        return {"raw_text": response.text}
