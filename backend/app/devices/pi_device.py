"""PI 设备定义。"""

import requests

from app.core.config import get_settings
from app.devices.base import BaseDevice
from app.domain.device_action import ActionSpec


def _request_pi(method: str, path: str) -> dict:
    """调用 PI 远程接口。"""
    settings = get_settings()
    base_url = settings.apis.pi.base_url.rstrip("/")
    response = requests.request(
        method=method,
        url=f"{base_url}{path}",
        timeout=settings.apis.pi.timeout,
    )
    response.raise_for_status()
    return response.json()


def build_pi_device(sim_mode: bool) -> BaseDevice:
    """构建 PI 设备实例。"""
    settings = get_settings()
    return BaseDevice(
        key="pi_2278",
        name="pi_2278",
        category="PI 合成系统",
        device_type="PISynthesisSystem",
        location="A-301",
        sim_mode=sim_mode,
        connection={"base_url": settings.apis.pi.base_url},
        actions=[
            ActionSpec(
                action_key="pi.health_check",
                name="健康检查",
                description="检查 PI 服务健康状态",
                executor=lambda _params, _context: _request_pi("GET", "/health"),
            ),
            ActionSpec(
                action_key="pi.power_on",
                name="启动",
                description="触发 PI 启动按钮",
                executor=lambda _params, _context: _request_pi("POST", "/ui/start"),
            ),
            ActionSpec(
                action_key="pi.pause",
                name="暂停",
                description="触发 PI 暂停按钮",
                executor=lambda _params, _context: _request_pi("POST", "/ui/pause"),
            ),
            ActionSpec(
                action_key="pi.power_off",
                name="停止",
                description="触发 PI 停止按钮",
                executor=lambda _params, _context: _request_pi("POST", "/ui/stop"),
            ),
        ],
    )
