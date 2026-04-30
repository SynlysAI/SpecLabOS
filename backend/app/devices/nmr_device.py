"""NMR 设备定义。"""

from typing import Any

import requests

from app.core.config import get_settings
from app.devices.base import BaseDevice
from app.domain.device_action import ActionSpec


def _request_nmr(method: str, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    """调用 NMR 远程接口。"""
    settings = get_settings()
    base_url = settings.apis.nmr.base_url.rstrip("/")
    response = requests.request(
        method=method,
        url=f"{base_url}{path}",
        timeout=settings.apis.nmr.timeout,
        json=params if method.upper() != "GET" else None,
        params=params if method.upper() == "GET" else None,
    )
    response.raise_for_status()
    try:
        return response.json()
    except ValueError:
        return {"raw_text": response.text}


def _build_executor(method: str, path: str):
    """构造 NMR 接口执行器。"""

    def _executor(params: dict[str, Any], _context: dict[str, Any]) -> dict[str, Any]:
        return _request_nmr(method, path, params=params)

    return _executor


def build_nmr_device(sim_mode: bool) -> BaseDevice:
    """构建 NMR 设备实例。"""
    settings = get_settings()
    return BaseDevice(
        key="nmr_2278",
        name="nmr_2278",
        category="核磁共振仪",
        device_type="NMRSpectrometer",
        location="A-203",
        sim_mode=sim_mode,
        connection={
            "base_url": settings.apis.nmr.base_url,
            "timeout": settings.apis.nmr.timeout,
        },
        actions=[
            ActionSpec(
                action_key="nmr.upload_task_info",
                name="下发检测参数",
                description="向 NMR 服务提交 task_info 参数列表",
                parameter_schema=[
                    {
                        "name": "task_info",
                        "type": "json",
                        "required": True,
                        "description": "核磁任务参数列表",
                    }
                ],
                executor=_build_executor("POST", "/task/info"),
            ),
            ActionSpec(
                action_key="nmr.start_task",
                name="开始任务",
                description="启动指定 batch_id 的核磁任务",
                parameter_schema=[
                    {
                        "name": "batch_id",
                        "type": "number",
                        "required": True,
                        "description": "核磁批次编号",
                    }
                ],
                executor=_build_executor("POST", "/task/start"),
            ),
            ActionSpec(
                action_key="nmr.get_task_status",
                name="查询任务状态",
                description="查询指定 batch_id 的核磁任务状态",
                parameter_schema=[
                    {
                        "name": "batch_id",
                        "type": "number",
                        "required": True,
                        "description": "核磁批次编号",
                    }
                ],
                executor=_build_executor("GET", "/task/status"),
            ),
            ActionSpec(
                action_key="nmr.list_templates",
                name="查询模板",
                description="查询 NMR 模板列表",
                parameter_schema=[],
                executor=_build_executor("GET", "/check"),
            ),
            ActionSpec(
                action_key="nmr.change_params",
                name="修改运行参数",
                description="修改 NMR 参数时间戳和参数列表",
                parameter_schema=[
                    {
                        "name": "stamp",
                        "type": "number",
                        "required": True,
                        "description": "参数时间戳或批次标识",
                    },
                    {
                        "name": "params",
                        "type": "json",
                        "required": True,
                        "description": "参数名与参数值列表",
                    },
                ],
                executor=_build_executor("POST", "/param/change"),
            ),
            ActionSpec(
                action_key="nmr.agv_interact",
                name="AGV 交互",
                description="执行 NMR AGV 上下料交互",
                parameter_schema=[
                    {
                        "name": "payload",
                        "type": "json",
                        "required": False,
                        "description": "AGV 请求参数",
                    }
                ],
                executor=lambda params, _context: _request_nmr(
                    "POST", "/agv", params=params.get("payload", {})
                ),
            ),
        ],
    )
