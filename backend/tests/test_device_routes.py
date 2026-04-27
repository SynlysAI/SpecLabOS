"""设备路由测试。"""

from fastapi.testclient import TestClient

from main import app


def test_list_devices_returns_items():
    """验证设备列表接口返回 items 列表。"""
    client = TestClient(app)

    response = client.get("/api/devices")

    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert isinstance(data["items"], list)
