"""日志路由测试。"""

from fastapi.testclient import TestClient

from main import app


def test_list_logs_returns_items():
    """验证日志列表接口返回标准化日志列表结构。"""
    client = TestClient(app)

    response = client.get("/api/logs")

    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert isinstance(data["items"], list)
    if data["items"]:
        first_item = data["items"][0]
        assert "id" in first_item
        assert "level" in first_item
        assert "source" in first_item
        assert "service_name" in first_item
        assert "message" in first_item
        assert "created_at" in first_item
