"""工作流路由测试。"""

from fastapi.testclient import TestClient

from main import app


def test_list_workflows_returns_items():
    """验证工作流列表接口返回精确的空列表响应。"""
    client = TestClient(app)

    response = client.get("/api/workflows")

    assert response.status_code == 200
    assert response.json() == {"items": []}
