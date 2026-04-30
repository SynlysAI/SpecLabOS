"""工作流路由测试。"""

from fastapi.testclient import TestClient

from main import app


def test_list_workflows_returns_items():
    """验证工作流列表接口返回列表结构。"""
    client = TestClient(app)

    response = client.get("/api/workflows")

    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert isinstance(data["items"], list)


def test_list_workflow_runs_returns_items():
    """验证运行列表接口返回列表结构。"""
    client = TestClient(app)

    response = client.get("/api/workflow-runs")

    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert isinstance(data["items"], list)


def test_get_workflow_run_detail_returns_detail():
    """验证运行详情接口返回单条详情。"""
    client = TestClient(app)

    response = client.get("/api/workflow-runs/RUN-20260427-001")

    assert response.status_code == 200
    data = response.json()
    assert data["run_id"] == "RUN-20260427-001"
    assert isinstance(data["steps"], list)


def test_create_workflow_returns_ids():
    """验证工作流创建接口返回定义和运行编号。"""
    client = TestClient(app)

    response = client.post(
        "/api/workflows",
        json={
            "name": "nmr_status_flow",
            "device_key": "nmr_2278",
            "steps": [
                {
                    "step_id": "step-1",
                    "device_key": "nmr_2278",
                    "action_key": "nmr.upload_task_info",
                    "display_name": "NMR 参数下发",
                    "params": {"task_info": [{"sample_id": "S-001"}]},
                    "confirm_params": {},
                }
            ],
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert "workflow_id" in data
    assert "run_id" in data

    runs_response = client.get("/api/workflow-runs")
    runs_data = runs_response.json()
    assert len(runs_data["items"]) >= 1


def test_create_workflow_rejects_multiple_devices():
    """验证工作流创建接口拒绝多设备混排。"""
    client = TestClient(app)

    response = client.post(
        "/api/workflows",
        json={
            "name": "mixed_flow",
            "device_key": "nmr_2278",
            "steps": [
                {
                    "step_id": "step-1",
                    "device_key": "nmr_2278",
                    "action_key": "nmr.upload_task_info",
                    "display_name": "NMR 参数下发",
                    "params": {"task_info": [{"sample_id": "S-001"}]},
                    "confirm_params": {},
                },
                {
                    "step_id": "step-2",
                    "device_key": "gpc_2278",
                    "action_key": "gpc.initialize",
                    "display_name": "GPC 初始化",
                    "params": {},
                    "confirm_params": {},
                },
            ],
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "当前仅支持单设备工作流编排"
