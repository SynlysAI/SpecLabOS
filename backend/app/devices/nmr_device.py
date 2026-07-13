"""NMR 设备定义。"""

from typing import Any

import requests

from app.core.config import get_settings
from app.devices.registry import capability, device, local_executor
from app.domain.capability import DeviceCapability
from app.domain.device import DeviceResource


@device
class NMRDevice(DeviceResource):
    """NMR 核磁共振仪。"""

    device_id: str = "nmr_2278"
    name: str = "nmr_2278"
    category: str = "核磁共振仪"
    device_type: str = "NMRSpectrometer"
    location: str = "A-203"


@local_executor("nmr_2278", "nmr.upload_task_info")
def nmr_upload_task_info_executor(
    params: dict[str, Any],
    context: dict[str, Any],
) -> dict[str, Any]:
    """下发 NMR 检测参数。

    Args:
        params: 执行参数。
        context: 运行上下文。

    Returns:
        NMR 服务响应。
    """
    return _request_nmr("POST", "/task/info", params=params)


@local_executor("nmr_2278", "nmr.start_task")
def nmr_start_task_executor(
    params: dict[str, Any],
    context: dict[str, Any],
) -> dict[str, Any]:
    """启动 NMR 任务。

    Args:
        params: 执行参数。
        context: 运行上下文。

    Returns:
        NMR 服务响应。
    """
    return _request_nmr("POST", "/task/start", params=params)


@local_executor("nmr_2278", "nmr.get_task_status")
def nmr_get_task_status_executor(
    params: dict[str, Any],
    context: dict[str, Any],
) -> dict[str, Any]:
    """查询 NMR 任务状态。

    Args:
        params: 执行参数。
        context: 运行上下文。

    Returns:
        NMR 服务响应。
    """
    return _request_nmr("GET", "/task/status", params=params)


@local_executor("nmr_2278", "nmr.list_templates")
def nmr_list_templates_executor(
    params: dict[str, Any],
    context: dict[str, Any],
) -> dict[str, Any]:
    """查询 NMR 模板列表。

    Args:
        params: 执行参数。
        context: 运行上下文。

    Returns:
        NMR 服务响应。
    """
    return _request_nmr("GET", "/check", params=params)


@local_executor("nmr_2278", "nmr.change_params")
def nmr_change_params_executor(
    params: dict[str, Any],
    context: dict[str, Any],
) -> dict[str, Any]:
    """修改 NMR 运行参数。

    Args:
        params: 执行参数。
        context: 运行上下文。

    Returns:
        NMR 服务响应。
    """
    return _request_nmr("POST", "/param/change", params=params)


@local_executor("nmr_2278", "nmr.agv_interact")
def nmr_agv_interact_executor(
    params: dict[str, Any],
    context: dict[str, Any],
) -> dict[str, Any]:
    """执行 NMR AGV 交互。

    Args:
        params: 执行参数。
        context: 运行上下文。

    Returns:
        NMR 服务响应。
    """
    return _request_nmr("POST", "/agv", params=params.get("payload", {}))


@capability("核磁共振仪")
def nmr_upload_task_info() -> DeviceCapability:
    """下发检测参数。"""
    return DeviceCapability(
        capability_key="nmr.upload_task_info",
        device_category="核磁共振仪",
        name="下发检测参数",
        description="向 NMR 服务提交 task_info 参数列表",
        step_mode="confirm",
        parameter_schema={
            "type": "object",
            "properties": {
                "task_info": {"type": "array", "description": "核磁任务参数列表"},
            },
            "required": ["task_info"],
        },
    )


@capability("核磁共振仪")
def nmr_start_task() -> DeviceCapability:
    """开始任务。"""
    return DeviceCapability(
        capability_key="nmr.start_task",
        device_category="核磁共振仪",
        name="开始任务",
        description="启动指定 batch_id 的核磁任务",
        step_mode="auto",
        parameter_schema={
            "type": "object",
            "properties": {
                "batch_id": {"type": "number", "description": "核磁批次编号"},
            },
            "required": ["batch_id"],
        },
    )


@capability("核磁共振仪")
def nmr_get_task_status() -> DeviceCapability:
    """查询任务状态。"""
    return DeviceCapability(
        capability_key="nmr.get_task_status",
        device_category="核磁共振仪",
        name="查询任务状态",
        description="查询指定 batch_id 的核磁任务状态",
        step_mode="auto",
        parameter_schema={
            "type": "object",
            "properties": {
                "batch_id": {"type": "number", "description": "核磁批次编号"},
            },
            "required": ["batch_id"],
        },
    )


@capability("核磁共振仪")
def nmr_list_templates() -> DeviceCapability:
    """查询模板。"""
    return DeviceCapability(
        capability_key="nmr.list_templates",
        device_category="核磁共振仪",
        name="查询模板",
        description="查询 NMR 模板列表",
        step_mode="auto",
    )


@capability("核磁共振仪")
def nmr_change_params() -> DeviceCapability:
    """修改运行参数。"""
    return DeviceCapability(
        capability_key="nmr.change_params",
        device_category="核磁共振仪",
        name="修改运行参数",
        description="修改 NMR 参数时间戳和参数列表",
        step_mode="confirm",
        parameter_schema={
            "type": "object",
            "properties": {
                "stamp": {"type": "number", "description": "参数时间戳或批次标识"},
                "params": {"type": "array", "description": "参数名与参数值列表"},
            },
            "required": ["stamp", "params"],
        },
    )


@capability("核磁共振仪")
def nmr_agv_interact() -> DeviceCapability:
    """AGV 交互。"""
    return DeviceCapability(
        capability_key="nmr.agv_interact",
        device_category="核磁共振仪",
        name="AGV 交互",
        description="执行 NMR AGV 上下料交互",
        step_mode="auto",
        parameter_schema={
            "type": "object",
            "properties": {
                "payload": {"type": "object", "description": "AGV 请求参数"},
            },
        },
    )


def _request_nmr(
    method: str,
    path: str,
    params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """调用 NMR 远程接口。

    Args:
        method: HTTP 方法。
        path: 接口路径。
        params: 请求参数。

    Returns:
        NMR 服务响应。
    """
    settings = get_settings()
    base_url = settings.apis.nmr.base_url.rstrip("/")
    request_params = dict(params or {})
    timeout = request_params.pop("timeout", settings.apis.nmr.timeout)
    response = requests.request(
        method=method,
        url=f"{base_url}{path}",
        timeout=timeout,
        json=request_params if method.upper() != "GET" else None,
        params=request_params if method.upper() == "GET" else None,
    )
    response.raise_for_status()
    try:
        return response.json()
    except ValueError:
        return {"raw_text": response.text}
