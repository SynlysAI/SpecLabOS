"""Raman 设备定义。"""

from typing import Any

import requests

from app.core.config import get_settings
from app.devices.base import BaseDevice
from app.domain.device_action import ActionSpec


def _request_raman(
    method: str,
    base_url: str,
    path: str,
    payload: dict[str, Any] | None = None,
    params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """调用 Raman 远程接口。"""
    response = requests.request(
        method=method,
        url=f"{base_url.rstrip('/')}{path}",
        timeout=get_settings().apis.raman.timeout,
        json=payload,
        params=params,
    )
    response.raise_for_status()
    try:
        return response.json()
    except ValueError:
        return {"raw_text": response.text}


def build_raman_device(sim_mode: bool) -> BaseDevice:
    """构建 Raman 设备实例。"""
    settings = get_settings()
    return BaseDevice(
        key="raman_2278",
        name="raman_2278",
        category="拉曼光谱仪",
        device_type="RamanSpectrometer",
        location="A-118",
        sim_mode=sim_mode,
        connection={
            "capture_base_url": settings.apis.raman.capture_base_url,
            "result_base_url": settings.apis.raman.result_base_url,
        },
        actions=[
            ActionSpec(
                action_key="raman.capture",
                name="下发采集任务",
                description="向 Raman 服务下发采集任务",
                parameter_schema=[
                    {
                        "name": "req_id",
                        "type": "string",
                        "required": True,
                        "description": "请求编号",
                    },
                    {
                        "name": "capture",
                        "type": "json",
                        "required": True,
                        "description": "采集任务 body 参数",
                    },
                ],
                executor=lambda params, _context: _request_raman(
                    "POST",
                    settings.apis.raman.capture_base_url,
                    "/raman/jy/capture",
                    payload={
                        "req_id": params.get("req_id"),
                        "capture": params.get("capture", {}),
                    },
                ),
            ),
            ActionSpec(
                action_key="raman.camera_focus",
                name="镜头对焦",
                description="自动对焦 Raman 设备镜头",
                parameter_schema=[
                    {
                        "name": "rt",
                        "type": "number",
                        "required": True,
                        "description": "上限",
                    },
                    {
                        "name": "rb",
                        "type": "number",
                        "required": True,
                        "description": "下限",
                    },
                    {
                        "name": "s",
                        "type": "number",
                        "required": True,
                        "description": "步长",
                    },
                ],
                executor=lambda params, _context: _request_raman(
                    "POST",
                    settings.apis.raman.capture_base_url,
                    "/raman/jy/camera",
                    payload={
                        "rt": params.get("rt", 8000),
                        "rb": params.get("rb", 5000),
                        "s": params.get("s", 3),
                        "method": 0,
                    },
                ),
            ),
            ActionSpec(
                action_key="raman.get_result",
                name="查询任务结果",
                description="查询 Raman 采集任务状态或结果",
                parameter_schema=[
                    {
                        "name": "req_id",
                        "type": "string",
                        "required": True,
                        "description": "请求编号",
                    }
                ],
                executor=lambda params, _context: _request_raman(
                    "GET",
                    settings.apis.raman.result_base_url,
                    "/raman/jy/result",
                    params={"req_id": params.get("req_id")},
                ),
            ),
        ],
    )
