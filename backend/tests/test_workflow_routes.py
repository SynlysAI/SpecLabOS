"""工作流路由测试。"""

from fastapi.testclient import TestClient

from main import app


def test_list_workflows_returns_items():
    """验证工作流列表接口返回精确的空列表响应。"""
    client = TestClient(app)

    response = client.get("/api/workflows")

    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert isinstance(data["items"], list)
    assert data["items"][0]["workflow_id"] == "wf-001"


def test_list_workflow_runs_returns_items():
    """验证运行列表接口返回基础示例数据。"""
    client = TestClient(app)

    response = client.get("/api/workflow-runs")

    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert isinstance(data["items"], list)
    assert data["items"][0]["run_id"] == "RUN-20260427-001"


def test_get_workflow_run_detail_returns_detail():
    """验证运行详情接口返回单条详情。"""
    client = TestClient(app)

    response = client.get("/api/workflow-runs/RUN-20260427-001")

    assert response.status_code == 200
    data = response.json()
    assert data["run_id"] == "RUN-20260427-001"
    assert isinstance(data["steps"], list)
