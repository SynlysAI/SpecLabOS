"""SmartAccess 路由测试。"""

from types import SimpleNamespace

from fastapi.testclient import TestClient

from app.api.routes import smartaccess
from main import app


def _workflow_payload() -> dict:
    """构造 SmartAccess workflow 快照。

    Returns:
        workflow 字典。
    """
    return {
        "metadata": {
            "workflow_id": "wf_weixin",
            "template_id": "tpl_weixin",
            "template_version": "1.0.0",
            "anchor_profile": "weixin",
        },
        "steps": [{"id": "open", "anchor_id": "open", "action": "click"}],
    }


def test_publish_and_list_smartaccess_template(fake_smartaccess_service) -> None:
    """验证 SmartAccess 模板发布和列表接口。"""
    client = TestClient(app)

    response = client.post(
        "/api/smartaccess/templates/publish",
        json={
            "template_id": "tpl_weixin",
            "template_version": "1.0.0",
            "workflow_id": "wf_weixin",
            "name": "微信流程",
            "anchor_profile": "weixin",
            "source_device_id": "weixin",
            "published_by": "smartaccess",
            "workflow": _workflow_payload(),
        },
    )

    assert response.status_code == 200
    assert response.json()["template_id"] == "tpl_weixin"

    list_response = client.get("/api/smartaccess/templates")
    assert list_response.status_code == 200
    assert any(
        item["template_id"] == "tpl_weixin"
        for item in list_response.json()["items"]
    )


def test_smartaccess_routes_require_bearer_token_when_configured(
    fake_smartaccess_service,
    monkeypatch,
) -> None:
    """验证配置 SmartAccess API Token 后路由需要 Bearer Token。"""
    monkeypatch.setattr(
        smartaccess,
        "get_settings",
        lambda: SimpleNamespace(
            smartaccess=SimpleNamespace(api_token="dev-smartaccess-token")
        ),
        raising=False,
    )
    client = TestClient(app)

    rejected_response = client.get("/api/smartaccess/templates")
    accepted_response = client.get(
        "/api/smartaccess/templates",
        headers={"Authorization": "Bearer dev-smartaccess-token"},
    )

    assert rejected_response.status_code == 401
    assert accepted_response.status_code == 200


def test_create_smartaccess_run_and_append_event(fake_smartaccess_service) -> None:
    """验证 SmartAccess 运行创建和状态事件回传。"""
    client = TestClient(app)
    client.post(
        "/api/smartaccess/templates/publish",
        json={
            "template_id": "tpl_weixin_run",
            "template_version": "1.0.0",
            "workflow_id": "wf_weixin",
            "name": "微信流程",
            "anchor_profile": "weixin",
            "source_device_id": "weixin",
            "published_by": "smartaccess",
            "workflow": _workflow_payload(),
        },
    )

    run_response = client.post(
        "/api/smartaccess/runs",
        json={
            "template_id": "tpl_weixin_run",
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
            "event_id": f"evt-route-{run_id}",
            "event_type": "run.started",
            "status": "running",
            "payload": {},
        },
    )

    assert event_response.status_code == 200

    list_response = client.get("/api/smartaccess/runs")
    assert list_response.status_code == 200
    assert any(item["run_id"] == run_id for item in list_response.json()["items"])

    detail_response = client.get(f"/api/smartaccess/runs/{run_id}")
    assert detail_response.json()["status"] == "running"


def test_append_smartaccess_event_rejects_missing_run(fake_smartaccess_service) -> None:
    """验证不存在的 SmartAccess 运行事件回传返回 404。"""
    client = TestClient(app)

    response = client.post(
        "/api/smartaccess/runs/missing-run/events",
        json={
            "event_id": "evt-route-missing-run",
            "event_type": "run.started",
            "status": "running",
            "payload": {},
        },
    )

    assert response.status_code == 404


def test_unified_workflow_runs_include_smartaccess_source(
    fake_smartaccess_service,
) -> None:
    """验证统一任务列表包含 SmartAccess 来源。"""
    client = TestClient(app)
    client.post(
        "/api/smartaccess/templates/publish",
        json={
            "template_id": "tpl_weixin_list",
            "template_version": "1.0.0",
            "workflow_id": "wf_weixin",
            "name": "微信流程",
            "anchor_profile": "weixin",
            "source_device_id": "weixin",
            "published_by": "smartaccess",
            "workflow": _workflow_payload(),
        },
    )
    client.post(
        "/api/smartaccess/runs",
        json={
            "template_id": "tpl_weixin_list",
            "template_version": "1.0.0",
            "device_id": "weixin",
            "requested_by": "admin",
        },
    )

    response = client.get("/api/workflow-runs")

    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert all("source" in item for item in data["items"])
    assert any(item["source"] == "smartaccess" for item in data["items"])
