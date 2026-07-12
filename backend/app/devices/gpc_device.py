"""GPC 设备定义。"""

from typing import Any

import requests

from app.core.config import get_settings
from app.devices.registry import capability, device, local_executor
from app.domain.capability import DeviceCapability
from app.domain.device import DeviceResource


@device
class GPCDevice(DeviceResource):
    """GPC 凝胶渗透色谱仪。"""

    device_id: str = "gpc_2278"
    name: str = "gpc_2278"
    category: str = "凝胶渗透色谱仪"
    device_type: str = "GPCAnalyzer"
    location: str = "A-105"


@local_executor("gpc_2278", "gpc.initialize")
def gpc_initialize_executor(
    params: dict[str, Any],
    context: dict[str, Any],
) -> dict[str, Any]:
    """执行 GPC 初始化。

    Args:
        params: 执行参数。
        context: 运行上下文。

    Returns:
        GPC 服务响应。
    """
    return _request_gpc("POST", "/device/action", {"action": "初始化"})


@local_executor("gpc_2278", "gpc.pause")
def gpc_pause_executor(
    params: dict[str, Any],
    context: dict[str, Any],
) -> dict[str, Any]:
    """执行 GPC 暂停。

    Args:
        params: 执行参数。
        context: 运行上下文。

    Returns:
        GPC 服务响应。
    """
    return _request_gpc("POST", "/device/action", {"action": "暂停"})


@local_executor("gpc_2278", "gpc.reset")
def gpc_reset_executor(
    params: dict[str, Any],
    context: dict[str, Any],
) -> dict[str, Any]:
    """执行 GPC 复位。

    Args:
        params: 执行参数。
        context: 运行上下文。

    Returns:
        GPC 服务响应。
    """
    return _request_gpc("POST", "/device/action", {"action": "复位"})


@local_executor("gpc_2278", "gpc.start_project")
def gpc_start_project_executor(
    params: dict[str, Any],
    context: dict[str, Any],
) -> dict[str, Any]:
    """执行 GPC 项目启动。

    Args:
        params: 执行参数。
        context: 运行上下文。

    Returns:
        GPC 服务响应。
    """
    return _request_gpc("POST", "/project/start")


@local_executor("gpc_2278", "gpc.get_device_status_detail")
def gpc_status_detail_executor(
    params: dict[str, Any],
    context: dict[str, Any],
) -> dict[str, Any]:
    """查询 GPC 设备明细状态。

    Args:
        params: 执行参数。
        context: 运行上下文。

    Returns:
        GPC 服务响应。
    """
    return _request_gpc("POST", "/device/status")


@local_executor("gpc_2278", "gpc.get_current_tasks")
def gpc_current_tasks_executor(
    params: dict[str, Any],
    context: dict[str, Any],
) -> dict[str, Any]:
    """查询 GPC 当前批次记录。

    Args:
        params: 执行参数。
        context: 运行上下文。

    Returns:
        GPC 服务响应。
    """
    return _request_gpc("GET", "/project/get-current-tasks")


@local_executor("gpc_2278", "gpc.upload_task_data")
def gpc_upload_task_data_executor(
    params: dict[str, Any],
    context: dict[str, Any],
) -> dict[str, Any]:
    """上传 GPC 批次任务数据。

    Args:
        params: 执行参数。
        context: 运行上下文。

    Returns:
        GPC 服务响应。
    """
    return _request_gpc(
        "POST",
        "/project/upload-task-data",
        params.get("task_data", []),
    )


@capability("凝胶渗透色谱仪")
def gpc_initialize() -> DeviceCapability:
    """初始化。"""
    return DeviceCapability(
        capability_key="gpc.initialize",
        device_category="凝胶渗透色谱仪",
        name="初始化",
        description="调用 GPC 初始化动作",
        step_mode="auto",
    )


@capability("凝胶渗透色谱仪")
def gpc_pause() -> DeviceCapability:
    """暂停。"""
    return DeviceCapability(
        capability_key="gpc.pause",
        device_category="凝胶渗透色谱仪",
        name="暂停",
        description="调用 GPC 暂停动作",
        step_mode="auto",
    )


@capability("凝胶渗透色谱仪")
def gpc_reset() -> DeviceCapability:
    """复位。"""
    return DeviceCapability(
        capability_key="gpc.reset",
        device_category="凝胶渗透色谱仪",
        name="复位",
        description="调用 GPC 复位动作",
        step_mode="auto",
    )


@capability("凝胶渗透色谱仪")
def gpc_start_project() -> DeviceCapability:
    """启动项目。"""
    return DeviceCapability(
        capability_key="gpc.start_project",
        device_category="凝胶渗透色谱仪",
        name="启动项目",
        description="启动 GPC 当前项目",
        step_mode="auto",
    )


@capability("凝胶渗透色谱仪")
def gpc_get_device_status_detail() -> DeviceCapability:
    """查询设备明细状态。"""
    return DeviceCapability(
        capability_key="gpc.get_device_status_detail",
        device_category="凝胶渗透色谱仪",
        name="查询设备明细状态",
        description="查询 GPC 耗材与模块状态",
        step_mode="auto",
    )


@capability("凝胶渗透色谱仪")
def gpc_get_current_tasks() -> DeviceCapability:
    """获取当前批次记录。"""
    return DeviceCapability(
        capability_key="gpc.get_current_tasks",
        device_category="凝胶渗透色谱仪",
        name="获取当前批次记录",
        description="获取 GPC 当前批次记录数据",
        step_mode="auto",
    )


@capability("凝胶渗透色谱仪")
def gpc_upload_task_data() -> DeviceCapability:
    """上传任务数据。"""
    return DeviceCapability(
        capability_key="gpc.upload_task_data",
        device_category="凝胶渗透色谱仪",
        name="上传任务数据",
        description="上传 GPC 批次任务数据",
        step_mode="auto",
        parameter_schema={
            "type": "object",
            "properties": {
                "task_data": {"type": "array", "description": "任务数据列表"},
            },
            "required": ["task_data"],
        },
    )


def _request_gpc(
    method: str,
    path: str,
    payload: Any | None = None,
) -> dict[str, Any]:
    """调用 GPC 远程接口。

    Args:
        method: HTTP 方法。
        path: 接口路径。
        payload: 请求体。

    Returns:
        GPC 服务响应。
    """
    settings = get_settings()
    base_url = settings.apis.gpc.base_url.rstrip("/")
    response = requests.request(
        method=method,
        url=f"{base_url}{path}",
        timeout=settings.apis.gpc.timeout,
        json=payload,
    )
    response.raise_for_status()
    try:
        return response.json()
    except ValueError:
        return {"raw_text": response.text}
