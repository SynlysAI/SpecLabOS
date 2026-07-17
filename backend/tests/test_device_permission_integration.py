"""设备权限端到端集成测试。

通过 FastAPI TestClient 验证:
- 设备列表接口带上 permission 字段
- admin 接口要求 admin role
- 设备控制接口按权限拦截
- 工作流提交按权限拦截
"""

import mongomock
import pytest
from fastapi.testclient import TestClient

_TEST_SECRET = "dev-secret-ai4ms-2026"


def _install_isolated_permission_service(monkeypatch) -> None:
    """为所有用到权限服务的路由模块注入隔离的 mongomock 实例。"""
    from app.repositories.device_permission_repository import (
        DevicePermissionRepository,
    )
    from app.services.device_permission_service import DevicePermissionService

    fake_db = mongomock.MongoClient()["speclabos_permission_test"]
    repo = DevicePermissionRepository(fake_db)
    service = DevicePermissionService(repo)

    import app.api.routes.admin as admin_module
    import app.api.routes.devices as devices_module
    import app.api.routes.workflows as workflows_module

    monkeypatch.setattr(
        devices_module, "get_device_permission_service", lambda: service
    )
    monkeypatch.setattr(
        workflows_module, "get_device_permission_service", lambda: service
    )
    monkeypatch.setattr(
        admin_module, "get_device_permission_service", lambda: service
    )


@pytest.fixture
def dev_client(monkeypatch):
    """提供关闭鉴权、使用隔离内存权限表的 TestClient。"""
    from app.core.config import get_settings
    import app.repositories.identity_repository as identity_repo

    monkeypatch.setattr(get_settings().auth, "enabled", False)
    monkeypatch.setattr(identity_repo, "_USER_CLIENT", mongomock.MongoClient())
    _install_isolated_permission_service(monkeypatch)

    from main import app

    return TestClient(app)


@pytest.fixture
def auth_client(monkeypatch):
    """提供开启鉴权、使用隔离内存权限表的 TestClient。"""
    from app.core.config import get_settings
    import app.repositories.identity_repository as identity_repo

    monkeypatch.setattr(get_settings().auth, "enabled", True)
    monkeypatch.setattr(get_settings().auth, "secret", _TEST_SECRET)
    monkeypatch.setattr(identity_repo, "_USER_CLIENT", mongomock.MongoClient())
    _install_isolated_permission_service(monkeypatch)

    from main import app

    return TestClient(app)


def _make_token(role: str, user_id: str, username: str) -> str:
    """使用测试密钥签发 token。"""
    from app.core import auth as auth_module

    return auth_module.generate_access_token(user_id, username, role)


def _seed_user_to_db(user_id: str, role: str, username: str):
    """把测试用户写入 mongomock 用户库。"""
    from app.repositories.identity_repository import UserRepository

    collection = UserRepository.get_collection()
    collection.delete_one({"user_id": user_id})
    collection.delete_one({"username": username})
    collection.insert_one(
        {
            "user_id": user_id,
            "username": username,
            "role": role,
            "status": "active",
            "organization": "",
            "password_hash": "x",
        }
    )


def test_list_devices_includes_permission_field(dev_client):
    """设备列表每项应包含 permission 字段。"""
    response = dev_client.get("/api/devices")
    assert response.status_code == 200
    items = response.json()["items"]
    assert items
    for item in items:
        assert "permission" in item
        assert item["permission"] in {"read", "control"}


def test_list_devices_detail_includes_permission(dev_client):
    """设备详情应包含 permission 字段。"""
    response = dev_client.get("/api/devices/ir_2278")
    assert response.status_code == 200
    assert response.json()["permission"] in {"read", "control"}


def test_admin_endpoints_accessible_in_dev_mode(dev_client):
    """鉴权关闭时,admin 接口应被 dev admin 访问。"""
    resp = dev_client.get("/api/admin/users")
    assert resp.status_code == 200


def test_admin_replace_user_devices_e2e(dev_client):
    """完整流程:管理员设置用户可控设备 -> 写入权限表。"""
    _seed_user_to_db("u_e2e", "user", "e2e_user")
    resp = dev_client.put(
        "/api/admin/users/u_e2e/devices",
        json={"device_keys": ["ir_2278", "hplc_001"]},
    )
    assert resp.status_code == 200
    payload = resp.json()
    assert payload["user_id"] == "u_e2e"
    assert set(payload["device_keys"]) == {"ir_2278", "hplc_001"}

    # 反查该设备的授权用户
    resp = dev_client.get("/api/admin/devices/ir_2278/users")
    assert resp.status_code == 200
    assert resp.json()["user_ids"] == ["u_e2e"]


def test_admin_partial_grant_revoke(dev_client):
    """单点授权 + 撤销。"""
    _seed_user_to_db("u_p1", "user", "p1_user")
    resp = dev_client.post("/api/admin/users/u_p1/devices/ir_2278")
    assert resp.status_code == 200
    assert "ir_2278" in resp.json()["device_keys"]

    resp = dev_client.delete("/api/admin/users/u_p1/devices/ir_2278")
    assert resp.status_code == 200
    assert "ir_2278" not in resp.json()["device_keys"]


def test_admin_endpoints_blocked_for_non_admin(auth_client):
    """开启鉴权后,普通用户访问 admin 接口应被拒绝。"""
    _seed_user_to_db("u_limited", "user", "limited")
    token = _make_token("user", "u_limited", "limited")

    resp = auth_client.get(
        "/api/admin/users",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 403


def test_admin_endpoints_blocked_without_token(auth_client):
    """开启鉴权后,无 token 访问 admin 接口应被拒绝。"""
    resp = auth_client.get("/api/admin/users")
    assert resp.status_code == 401


def test_workflow_submit_blocked_without_permission(auth_client):
    """开启鉴权后,普通用户对未授权设备提交工作流应被拒绝。"""
    _seed_user_to_db("u_normal", "user", "normal_user")
    token = _make_token("user", "u_normal", "normal_user")

    payload = {
        "name": "测试工作流",
        "created_by": "normal_user",
        "device_key": "ir_2278",
        "steps": [
            {
                "step_id": "s1",
                "device_key": "ir_2278",
                "action_key": "ir.power_on",
                "display_name": "启动 IR",
            }
        ],
    }
    resp = auth_client.post(
        "/api/workflows",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 403


def test_workflow_submit_passes_after_grant(auth_client):
    """授权后,普通用户可以提交工作流。"""
    _seed_user_to_db("u_normal2", "user", "normal2")
    _seed_user_to_db("u_admin1", "admin", "admin_user")
    user_token = _make_token("user", "u_normal2", "normal2")
    admin_token = _make_token("admin", "u_admin1", "admin_user")

    grant_resp = auth_client.put(
        "/api/admin/users/u_normal2/devices",
        json={"device_keys": ["ir_2278"]},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert grant_resp.status_code == 200

    payload = {
        "name": "测试工作流",
        "created_by": "normal2",
        "device_key": "ir_2278",
        "steps": [
            {
                "step_id": "s1",
                "device_key": "ir_2278",
                "action_key": "ir.power_on",
                "display_name": "启动 IR",
            }
        ],
    }
    resp = auth_client.post(
        "/api/workflows",
        json=payload,
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert resp.status_code == 200


def test_admin_can_see_other_users_permission(auth_client):
    """admin 能查询其他用户的可控设备列表。"""
    _seed_user_to_db("u_admin2", "admin", "admin2")
    _seed_user_to_db("u_target", "user", "target_user")
    admin_token = _make_token("admin", "u_admin2", "admin2")

    auth_client.put(
        "/api/admin/users/u_target/devices",
        json={"device_keys": ["ir_2278"]},
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    resp = auth_client.get(
        "/api/admin/users/u_target/devices",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["device_keys"] == ["ir_2278"]
