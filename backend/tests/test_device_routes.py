"""设备路由测试。"""

from fastapi.testclient import TestClient

from main import app


def test_list_devices_returns_items():
    """验证设备列表接口返回与 spectrum_alab 对齐的设备集合。"""
    client = TestClient(app)

    response = client.get("/api/devices")

    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert len(data["items"]) == 12
    assert data["items"][0]["key"] == "nmr_2278"
    assert data["items"][0]["image_url"] == "/api/device-images/NMRSpectrometer"
