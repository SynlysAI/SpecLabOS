"""GPC 设备定义。"""

from typing import Any

import requests

from app.core.config import get_settings
from app.devices.base import BaseDevice
from app.domain.device_action import ActionSpec


def _request_gpc(method: str, path: str, payload: Any | None = None) -> dict[str, Any]:
    """调用 GPC 远程接口。"""
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


def build_gpc_device(sim_mode: bool) -> BaseDevice:
    """构建 GPC 设备实例。"""
    settings = get_settings()
    return BaseDevice(
        key="gpc_2278",
        name="gpc_2278",
        category="凝胶渗透色谱仪",
        device_type="GPCAnalyzer",
        location="A-105",
        sim_mode=sim_mode,
        connection={"base_url": settings.apis.gpc.base_url},
        actions=[
            ActionSpec(
                action_key="gpc.initialize",
                name="初始化",
                description="调用 GPC 初始化动作",
                executor=lambda _params, _context: _request_gpc(
                    "POST", "/device/action", {"action": "初始化"}
                ),
            ),
            ActionSpec(
                action_key="gpc.pause",
                name="暂停",
                description="调用 GPC 暂停动作",
                executor=lambda _params, _context: _request_gpc(
                    "POST", "/device/action", {"action": "暂停"}
                ),
            ),
            ActionSpec(
                action_key="gpc.reset",
                name="复位",
                description="调用 GPC 复位动作",
                executor=lambda _params, _context: _request_gpc(
                    "POST", "/device/action", {"action": "复位"}
                ),
            ),
            ActionSpec(
                action_key="gpc.start_project",
                name="启动项目",
                description="启动 GPC 当前项目",
                executor=lambda _params, _context: _request_gpc("POST", "/project/start"),
            ),
            ActionSpec(
                action_key="gpc.get_device_status_detail",
                name="查询设备明细状态",
                description="查询 GPC 耗材与模块状态",
                executor=lambda _params, _context: _request_gpc("POST", "/device/status"),
            ),
            ActionSpec(
                action_key="gpc.get_current_tasks",
                name="获取当前批次记录",
                description="获取 GPC 当前批次记录数据",
                executor=lambda _params, _context: _request_gpc(
                    "GET", "/project/get-current-tasks"
                ),
            ),
            ActionSpec(
                action_key="gpc.upload_task_data",
                name="上传任务数据",
                description="上传 GPC 批次任务数据",
                parameter_schema=[
                    {
                        "name": "task_data",
                        "type": "json",
                        "required": True,
                        "description": "任务数据列表",
                    }
                ],
                executor=lambda params, _context: _request_gpc(
                    "POST", "/project/upload-task-data", params.get("task_data", [])
                ),
            ),
        ],
    )
