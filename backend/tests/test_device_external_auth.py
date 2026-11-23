"""设备路由外部 API Token 认证测试。"""

from fastapi.testclient import TestClient

from app.core.config import get_settings
from main import app


def _set_external_token(monkeypatch, token: str) -> None:
    """为当前测试注入统一外部 API Token。"""
    monkeypatch.setattr(get_settings().external_api, "api_token", token)


def test_devices_allows_anonymous(monkeypatch):
    """未提供认证信息时应保持匿名放行。"""
    _set_external_token(monkeypatch, "test-external-token")
    client = TestClient(app)
    response = client.get("/api/devices")
    assert response.status_code == 200
    assert isinstance(response.json()["items"], list)


def test_devices_accepts_external_api_token(monkeypatch):
    """统一外部 API Token 应通过校验并按只读服务主体处理。"""
    _set_external_token(monkeypatch, "test-external-token")
    client = TestClient(app)
    response = client.get(
        "/api/devices", headers={"Authorization": "Bearer test-external-token"}
    )
    assert response.status_code == 200
    payload = response.json()
    assert isinstance(payload["items"], list)
    assert all(item["permission"] == "read" for item in payload["items"])


def test_devices_rejects_invalid_token(monkeypatch):
    """提供了无法识别的凭证时应返回 401。"""
    _set_external_token(monkeypatch, "test-external-token")
    client = TestClient(app)
    response = client.get(
        "/api/devices", headers={"Authorization": "Bearer wrong-token"}
    )
    assert response.status_code == 401
