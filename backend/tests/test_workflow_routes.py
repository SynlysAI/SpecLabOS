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


def test_get_workflow_run_detail_supports_smartaccess_source():
    """验证统一运行详情接口兼容 SmartAccess 来源。"""
    client = TestClient(app)

    publish_response = client.post(
        "/api/smartaccess/templates/publish",
        json={
            "template_id": "tpl_workflow_detail",
            "template_version": "1.0.0",
            "workflow_id": "wf_weixin",
            "name": "微信流程",
            "anchor_profile": "weixin",
            "source_device_id": "weixin",
            "published_by": "smartaccess",
            "workflow": {
                "metadata": {
                    "workflow_id": "wf_weixin",
                    "template_id": "tpl_workflow_detail",
                    "template_version": "1.0.0",
                    "anchor_profile": "weixin",
                },
                "steps": [{"id": "open", "anchor_id": "open", "action": "click"}],
            },
        },
    )
    assert publish_response.status_code == 200

    run_response = client.post(
        "/api/smartaccess/runs",
        json={
            "template_id": "tpl_workflow_detail",
            "template_version": "1.0.0",
            "device_id": "weixin",
            "requested_by": "admin",
        },
    )
    assert run_response.status_code == 200
    run_id = run_response.json()["run_id"]
    event_response = client.post(
        f"/api/smartaccess/runs/{run_id}/events",
        json={
            "event_id": f"evt-workflow-route-{run_id}",
            "event_type": "run.started",
            "step_id": "open",
            "step_index": 0,
            "status": "running",
            "payload": {},
        },
    )
    assert event_response.status_code == 200

    response = client.get(f"/api/workflow-runs/{run_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["run_id"] == run_id
    assert data["source"] == "smartaccess"
    assert data["template_id"] == "tpl_workflow_detail"
    assert data["anchor_profile"] == "weixin"
    assert isinstance(data["events"], list)
    assert isinstance(data["steps"], list)


def test_list_workflow_runs_supports_smartaccess_source_filter():
    """验证统一运行列表支持按 SmartAccess 来源过滤。"""
    client = TestClient(app)
    publish_response = client.post(
        "/api/smartaccess/templates/publish",
        json={
            "template_id": "tpl_workflow_filter",
            "template_version": "1.0.0",
            "workflow_id": "wf_weixin",
            "name": "微信流程",
            "anchor_profile": "weixin",
            "source_device_id": "weixin",
            "published_by": "smartaccess",
            "workflow": {
                "metadata": {
                    "workflow_id": "wf_weixin",
                    "template_id": "tpl_workflow_filter",
                    "template_version": "1.0.0",
                    "anchor_profile": "weixin",
                },
                "steps": [{"id": "open", "anchor_id": "open", "action": "click"}],
            },
        },
    )
    assert publish_response.status_code == 200
    run_response = client.post(
        "/api/smartaccess/runs",
        json={
            "template_id": "tpl_workflow_filter",
            "template_version": "1.0.0",
            "device_id": "weixin",
            "requested_by": "admin",
        },
    )
    assert run_response.status_code == 200

    response = client.get("/api/workflow-runs", params={"source": "smartaccess"})

    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert data["items"]
    assert all(item["source"] == "smartaccess" for item in data["items"])
