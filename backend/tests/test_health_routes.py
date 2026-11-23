"""健康检查路由测试。"""

from fastapi.testclient import TestClient

from main import app


def test_health_returns_ok_json():
    """/health 应返回 200 与最小 JSON 状态体。"""
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "speclabos"}
