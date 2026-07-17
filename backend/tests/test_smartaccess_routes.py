"""SmartAccess 路由测试。"""

from types import SimpleNamespace

import mongomock
from fastapi.testclient import TestClient

from app.api.routes import smartaccess
from app.core import auth as auth_module
from app.core.config import get_settings
from app.repositories.device_permission_repository import (
    DevicePermissionRepository,
)
from app.repositories.identity_repository import UserRepository
from app.schemas.smartaccess import SmartAccessTemplatePublishRequest
from app.services.device_permission_service import DevicePermissionService
from main import app


_TEST_SECRET = "dev-secret-ai4ms-2026"


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


def _install_auth_user(monkeypatch, user_id: str, username: str) -> dict:
    """为 SmartAccess 路由测试安装隔离用户和权限服务。

    Args:
        monkeypatch: pytest monkeypatch 夹具。
        user_id: 测试用户 ID。
        username: 测试用户名。

    Returns:
        包含请求头和权限服务的测试上下文。
    """
    import app.repositories.identity_repository as identity_repo

    monkeypatch.setattr(get_settings().auth, "enabled", True)
    monkeypatch.setattr(get_settings().auth, "secret", _TEST_SECRET)
    monkeypatch.setattr(identity_repo, "_USER_CLIENT", mongomock.MongoClient())
    UserRepository.get_collection().insert_one(
        {
            "user_id": user_id,
            "username": username,
            "role": "user",
            "status": "active",
            "organization": "",
            "password_hash": "x",
        }
    )
    permission_repository = DevicePermissionRepository(
        mongomock.MongoClient()["smartaccess_permission_test"]
    )
    permission_service = DevicePermissionService(permission_repository)
    monkeypatch.setattr(
        smartaccess,
        "get_device_permission_service",
        lambda: permission_service,
    )
    token = auth_module.generate_access_token(user_id, username, "user")
    return {
        "headers": {"Authorization": f"Bearer {token}"},
        "permission_service": permission_service,
    }


def test_create_smartaccess_run_requires_device_control_permission(
    fake_smartaccess_service,
    monkeypatch,
) -> None:
    """验证用户 Token 下发 SmartAccess 运行需具备对应虚拟设备控制权限。"""
    user_id = "u_xiaoxu"
    username = "xiaoxu"
    context = _install_auth_user(monkeypatch, user_id, username)
    headers = context["headers"]
    permission_service = context["permission_service"]
    fake_smartaccess_service.publish_template(
        SmartAccessTemplatePublishRequest(
            template_id="tpl_vpn_test",
            template_version="1.0.0",
            workflow_id="wf_vpn",
            name="vpn导入弹窗测试",
            anchor_profile="vpn导入弹窗测试",
            source_device_id="vpn导入弹窗测试",
            published_by="smartaccess",
            workflow=_workflow_payload(),
        )
    )
    client = TestClient(app)

    payload = {
        "template_id": "tpl_vpn_test",
        "template_version": "1.0.0",
        "smartaccess_node_id": "vpn导入弹窗测试",
        "target_device_id": "vpn导入弹窗测试",
        "requested_by": username,
    }

    rejected_response = client.post(
        "/api/smartaccess/runs",
        headers=headers,
        json=payload,
    )
    permission_service.grant(
        user_id,
        "smartaccess:vpn导入弹窗测试",
        "admin",
    )
    accepted_response = client.post(
        "/api/smartaccess/runs",
        headers=headers,
        json=payload,
    )

    assert rejected_response.status_code == 403
    assert accepted_response.status_code == 200


def test_publish_smartaccess_template_grants_first_publisher_control(
    fake_smartaccess_service,
    monkeypatch,
) -> None:
    """验证普通用户首次发布 SmartAccess 虚拟设备时自动获得控制权限。"""
    user_id = "u_first_publisher"
    username = "first_publisher"
    context = _install_auth_user(monkeypatch, user_id, username)
    headers = context["headers"]
    permission_service = context["permission_service"]
    client = TestClient(app)

    response = client.post(
        "/api/smartaccess/templates/publish",
        headers=headers,
        json={
            "template_id": "tpl_first_device",
            "template_version": "1.0.0",
            "workflow_id": "wf_first_device",
            "name": "首次发布设备流程",
            "anchor_profile": "首次发布设备",
            "source_device_id": "首次发布设备",
            "published_by": username,
            "workflow": _workflow_payload(),
        },
    )

    assert response.status_code == 200
    assert permission_service.list_grants_by_device(
        "smartaccess:首次发布设备"
    )[0]["user_id"] == user_id


def test_publish_smartaccess_template_does_not_grant_when_device_has_grants(
    fake_smartaccess_service,
    monkeypatch,
) -> None:
    """验证已有授权关系的 SmartAccess 设备不会因普通用户发布而静默扩权。"""
    user_id = "u_second_publisher"
    username = "second_publisher"
    context = _install_auth_user(monkeypatch, user_id, username)
    headers = context["headers"]
    permission_service = context["permission_service"]
    permission_service.grant(
        "u_existing_owner",
        "smartaccess:已有授权设备",
        "admin",
    )
    client = TestClient(app)

    response = client.post(
        "/api/smartaccess/templates/publish",
        headers=headers,
        json={
            "template_id": "tpl_existing_device",
            "template_version": "1.0.0",
            "workflow_id": "wf_existing_device",
            "name": "已有授权设备流程",
            "anchor_profile": "已有授权设备",
            "source_device_id": "已有授权设备",
            "published_by": username,
            "workflow": _workflow_payload(),
        },
    )
    grants = permission_service.list_grants_by_device(
        "smartaccess:已有授权设备"
    )

    assert response.status_code == 200
    assert {item["user_id"] for item in grants} == {"u_existing_owner"}


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


def test_list_smartaccess_template_filters_source_device_id(
    fake_smartaccess_service,
) -> None:
    """验证 SmartAccess 模板列表可按发布执行端过滤。"""

    client = TestClient(app)
    for source_device_id in ("pc-xiaoxu", "pc-other"):
        response = client.post(
            "/api/smartaccess/templates/publish",
            json={
                "template_id": f"tpl_{source_device_id}",
                "template_version": "1.0.0",
                "workflow_id": f"wf_{source_device_id}",
                "name": f"{source_device_id} 流程",
                "anchor_profile": "weixin",
                "source_device_id": source_device_id,
                "published_by": "smartaccess",
                "workflow": _workflow_payload(),
            },
        )
        assert response.status_code == 200

    list_response = client.get(
        "/api/smartaccess/templates?source_device_id=pc-xiaoxu"
    )

    assert list_response.status_code == 200
    items = list_response.json()["items"]
    assert [item["source_device_id"] for item in items] == ["pc-xiaoxu"]


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
            "smartaccess_node_id": "weixin",
            "target_device_id": "weixin",
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
            "smartaccess_node_id": "weixin",
            "target_device_id": "weixin",
            "requested_by": "admin",
        },
    )

    response = client.get("/api/workflow-runs")

    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert all("source" in item for item in data["items"])
    assert any(item["source"] == "smartaccess" for item in data["items"])
