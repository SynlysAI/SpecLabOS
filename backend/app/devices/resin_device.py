"""树脂处理设备定义。"""

from typing import Any

import requests

from app.core.config import get_settings
from app.devices.base import BaseDevice
from app.domain.device_action import ActionSpec


def _request_resin(device_key: str, method: str, path: str, payload: dict[str, Any] | None = None):
    """调用 Resin 远程接口。"""
    settings = get_settings()
    base_url = (
        settings.apis.resin.devices.get(device_key)
        or settings.apis.resin.base_url
    ).rstrip("/")
    response = requests.request(
        method=method,
        url=f"{base_url}{path}",
        timeout=settings.apis.resin.timeout,
        json=payload,
    )
    response.raise_for_status()
    try:
        return response.json()
    except ValueError:
        return {"raw_text": response.text}


def build_resin_device(
    sim_mode: bool,
    key: str = "resin_2278",
    location: str = "B-201",
) -> BaseDevice:
    """构建树脂处理设备实例。"""
    settings = get_settings()
    return BaseDevice(
        key=key,
        name=key,
        category="树脂工作站",
        device_type="ResinWorkstation",
        location=location,
        sim_mode=sim_mode,
        connection={
            "base_url": settings.apis.resin.devices.get(key) or settings.apis.resin.base_url
        },
        actions=[
            ActionSpec(
                action_key="resin.health_check",
                name="健康检查",
                description="检查 Resin 工作站健康状态",
                executor=lambda _params, _context, device_key=key: _request_resin(
                    device_key, "GET", "/health"
                ),
            ),
            ActionSpec(
                action_key="resin.trigger_generate",
                name="触发解析",
                description="触发 Resin 解析实验方案",
                parameter_schema=[
                    {
                        "name": "experiment_plan",
                        "type": "string",
                        "required": True,
                        "description": "实验方案文本",
                    },
                    {
                        "name": "request_id",
                        "type": "string",
                        "required": False,
                        "description": "可选请求标识",
                    },
                ],
                executor=lambda params, _context, device_key=key: _request_resin(
                    device_key,
                    "POST",
                    "/api/v1/experiment/trigger",
                    {
                        "experiment_plan": params.get("experiment_plan", ""),
                        **(
                            {"request_id": params["request_id"]}
                            if params.get("request_id")
                            else {}
                        ),
                    },
                ),
            ),
            ActionSpec(
                action_key="resin.execute_process",
                name="执行流程",
                description="执行 Resin 工艺流程",
                parameter_schema=[
                    {
                        "name": "request_id",
                        "type": "string",
                        "required": False,
                        "description": "可选请求标识",
                    }
                ],
                executor=lambda params, _context, device_key=key: _request_resin(
                    device_key,
                    "POST",
                    "/api/v1/experiment/execute",
                    {"request_id": params["request_id"]} if params.get("request_id") else None,
                ),
            ),
            ActionSpec(
                action_key="resin.get_experiment_status",
                name="查询流程状态",
                description="查询 Resin 流程执行状态",
                executor=lambda _params, _context, device_key=key: _request_resin(
                    device_key, "GET", "/api/v1/experiment/status"
                ),
            ),
        ],
    )
