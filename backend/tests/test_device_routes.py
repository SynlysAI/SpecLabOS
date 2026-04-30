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
    device_keys = {item["key"] for item in data["items"]}
    assert {
        "nmr_2278",
        "gpc_2278",
        "pi_2278",
        "ir_2278",
        "raman_2278",
        "lcms_2278",
        "resin_2278",
        "resin_2278_2",
        "resin_1438",
        "metal_108",
        "cat_108",
        "micro_108",
    }.issubset(device_keys)
    assert data["items"][0]["image_url"] == "/api/device-images/NMRSpectrometer"


def test_list_device_actions_returns_items():
    """验证设备动作目录接口返回真实动作列表。"""
    client = TestClient(app)

    response = client.get("/api/devices/nmr_2278/actions")

    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert isinstance(data["items"], list)
    assert data["items"][0]["action_key"] == "nmr.upload_task_info"
    assert any(
        field["name"] == "task_info" and field["type"] == "json"
        for field in data["items"][0]["parameter_schema"]
    )


def test_list_raman_device_actions_returns_json_parameters():
    """验证 Raman 动作目录返回 JSON 参数定义。"""
    client = TestClient(app)

    response = client.get("/api/devices/raman_2278/actions")

    assert response.status_code == 200
    data = response.json()
    action_keys = {item["action_key"] for item in data["items"]}
    assert action_keys == {"raman.capture", "raman.get_result"}
    capture_action = next(item for item in data["items"] if item["action_key"] == "raman.capture")
    assert any(
        field["name"] == "capture" and field["type"] == "json"
        for field in capture_action["parameter_schema"]
    )


def test_list_pi_device_actions_filters_unimplemented_actions():
    """验证 PI 动作目录不暴露未实现动作。"""
    client = TestClient(app)

    response = client.get("/api/devices/pi_2278/actions")

    assert response.status_code == 200
    data = response.json()
    assert {item["action_key"] for item in data["items"]} == {
        "pi.health_check",
        "pi.power_on",
        "pi.pause",
        "pi.power_off",
    }
