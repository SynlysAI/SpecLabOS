"""工位设备定义。"""

import requests

from app.core.config import get_settings
from app.devices.base import BaseDevice
from app.domain.device_action import ActionSpec


def _request_station(device_action_key: str, action: str | None = None):
    """调用 Station 远程接口。"""
    settings = get_settings()
    base_url = settings.apis.station.base_url.rstrip("/")
    path = f"/{device_action_key}/status" if action is None else f"/{device_action_key}/action"
    payload = None if action is None else {"action": action}
    response = requests.request(
        method="POST",
        url=f"{base_url}{path}",
        timeout=settings.apis.station.timeout,
        json=payload,
    )
    response.raise_for_status()
    return response.json()


def build_station_device(
    sim_mode: bool,
    key: str = "station_001",
    device_type: str = "MicroCharacterizationDevice",
    category: str = "工位设备",
    location: str = "C-101",
) -> BaseDevice:
    """构建设备工位实例。"""
    settings = get_settings()
    device_action_key = key.split("_")[0]
    return BaseDevice(
        key=key,
        name=key,
        category=category,
        device_type=device_type,
        location=location,
        sim_mode=sim_mode,
        connection={"base_url": settings.apis.station.base_url},
        actions=[
            ActionSpec(
                action_key=f"{key}.check_status",
                name="检查状态",
                description=f"查询 {key} 当前状态",
                executor=lambda _params, _context, action_key=device_action_key: _request_station(
                    action_key
                ),
            ),
            ActionSpec(
                action_key=f"{key}.power_on",
                name="启动",
                description=f"启动 {key}",
                executor=lambda _params, _context, action_key=device_action_key: _request_station(
                    action_key, "启动"
                ),
            ),
            ActionSpec(
                action_key=f"{key}.power_off",
                name="停止",
                description=f"停止 {key}",
                executor=lambda _params, _context, action_key=device_action_key: _request_station(
                    action_key, "停止"
                ),
            ),
        ],
    )
