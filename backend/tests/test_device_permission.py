"""设备权限仓储与服务测试。"""

import mongomock
import pytest

from app.repositories.device_permission_repository import (
    DevicePermissionRepository,
)
from app.services.device_permission_service import DevicePermissionService


@pytest.fixture
def repository():
    """提供基于 mongomock 的权限仓储。"""
    client = mongomock.MongoClient()
    return DevicePermissionRepository(client["permission_test"])


@pytest.fixture
def service(repository):
    """提供绑定测试仓储的权限服务。"""
    return DevicePermissionService(repository)


def test_grant_and_has_access(repository):
    """授权后应能查询到记录。"""
    assert not repository.has_access("u1", "ir_2278")
    repository.grant("u1", "ir_2278", "admin_x")
    assert repository.has_access("u1", "ir_2278")
    assert not repository.has_access("u1", "hplc_001")
    assert not repository.has_access("u2", "ir_2278")


def test_grant_is_idempotent(repository):
    """重复授权不报错,且不覆盖原 granted_at。"""
    first = repository.grant("u1", "ir_2278", "admin_a")
    second = repository.grant("u1", "ir_2278", "admin_b")
    assert first["granted_by"] == "admin_a"
    assert second["granted_by"] == "admin_a"


def test_list_device_keys_by_user(repository):
    """查询用户可控设备列表。"""
    repository.grant("u1", "ir_2278", "admin")
    repository.grant("u1", "hplc_001", "admin")
    repository.grant("u2", "ir_2278", "admin")

    keys = repository.list_device_keys_by_user("u1")
    assert set(keys) == {"ir_2278", "hplc_001"}
    assert repository.list_device_keys_by_user("u2") == ["ir_2278"]
    assert repository.list_device_keys_by_user("u3") == []


def test_list_user_ids_by_device(repository):
    """查询设备授权用户列表。"""
    repository.grant("u1", "ir_2278", "admin")
    repository.grant("u2", "ir_2278", "admin")

    user_ids = repository.list_user_ids_by_device("ir_2278")
    assert set(user_ids) == {"u1", "u2"}
    assert repository.list_user_ids_by_device("hplc_001") == []


def test_revoke(repository):
    """撤销授权。"""
    repository.grant("u1", "ir_2278", "admin")
    assert repository.has_access("u1", "ir_2278")

    assert repository.revoke("u1", "ir_2278") is True
    assert not repository.has_access("u1", "ir_2278")
    assert repository.revoke("u1", "ir_2278") is False


def test_replace_user_devices_add_and_remove(repository):
    """覆盖式设置用户设备列表,应同时处理增删。"""
    repository.grant("u1", "ir_2278", "admin")
    repository.grant("u1", "hplc_001", "admin")

    repository.replace_user_devices("u1", ["ir_2278", "nmr_001"], "admin")

    assert set(repository.list_device_keys_by_user("u1")) == {
        "ir_2278",
        "nmr_001",
    }


def test_replace_device_users(repository):
    """覆盖式设置设备用户列表。"""
    repository.grant("u1", "ir_2278", "admin")
    repository.grant("u2", "ir_2278", "admin")

    repository.replace_device_users("ir_2278", ["u1", "u3"], "admin")

    assert set(repository.list_user_ids_by_device("ir_2278")) == {"u1", "u3"}


def test_unique_index_prevents_duplicate(repository):
    """同一 user + device 二次插入不会产生两条记录。"""
    repository.grant("u1", "ir_2278", "admin")
    repository.grant("u1", "ir_2278", "admin")
    grants = repository.list_grants_by_user("u1")
    assert len(grants) == 1


# ----- DevicePermissionService 单元测试 -----


def test_service_admin_bypasses_assert(service):
    """admin 用户应跳过权限检查。"""
    admin = {"user_id": "admin_1", "role": "admin"}
    service.assert_control(admin, ["ir_2278", "hplc_001", "anything"])


def test_service_assert_control_pass_when_granted(service):
    """普通用户对已授权设备应通过。"""
    user = {"user_id": "u1", "role": "user"}
    service.grant("u1", "ir_2278", "admin")
    service.assert_control(user, ["ir_2278"])


def test_service_assert_control_raises_when_missing(service):
    """普通用户对未授权设备应抛 403。"""
    from fastapi import HTTPException

    user = {"user_id": "u1", "role": "user"}
    with pytest.raises(HTTPException) as exc:
        service.assert_control(user, ["ir_2278"])
    assert exc.value.status_code == 403


def test_service_assert_control_raises_when_anonymous(service):
    """未登录用户对设备控制应抛 401。"""
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc:
        service.assert_control(None, ["ir_2278"])
    assert exc.value.status_code == 401


def test_service_assert_control_skips_empty_device_list(service):
    """空设备列表不触发任何校验。"""
    user = {"user_id": "u1", "role": "user"}
    service.assert_control(user, [])
    service.assert_control(user, [None, ""])


def test_service_list_user_device_keys_admin_returns_empty(service):
    """admin 返回空列表(语义为不限制)。"""
    admin = {"user_id": "admin_1", "role": "admin"}
    assert service.list_user_device_keys(admin) == []


def test_service_filter_allowed_device_keys(service):
    """过滤出用户有权限的设备子集。"""
    user = {"user_id": "u1", "role": "user"}
    service.grant("u1", "ir_2278", "admin")
    service.grant("u1", "hplc_001", "admin")

    result = service.filter_allowed_device_keys(
        user, ["ir_2278", "nmr_001", "hplc_001"]
    )
    assert set(result) == {"ir_2278", "hplc_001"}


def test_service_replace_user_devices(service):
    """服务层覆盖式授权。"""
    result = service.replace_user_devices("u1", ["ir_2278"], "admin")
    assert result == {"user_id": "u1", "device_keys": ["ir_2278"]}

    # 二次调用替换为新集合
    result = service.replace_user_devices("u1", ["hplc_001"], "admin")
    assert result == {"user_id": "u1", "device_keys": ["hplc_001"]}
