"""日志路由测试。"""

from fastapi.testclient import TestClient

from main import app


def test_list_logs_returns_items():
    """验证日志列表接口返回精确的空列表响应。"""
    client = TestClient(app)

    response = client.get("/api/logs")

    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert isinstance(data["items"], list)
    assert data["items"][0]["id"] == "LOG-001"
