"""设备注册表测试。"""

import pytest

from app.devices.factories import build_device, list_supported_categories
from app.devices.nmr_device import build_nmr_device
from app.devices.registry import DeviceRegistry


def test_registry_registers_device_and_actions():
    """验证注册表能够注册设备并暴露动作声明。"""
    registry = DeviceRegistry()
    device = build_nmr_device(sim_mode=True)

    registry.register(device)

    assert registry.get_device("nmr_2278").key == "nmr_2278"
    actions = registry.list_actions("nmr_2278")
    action_keys = [action.action_key for action in actions]
    assert "nmr.check_status" in action_keys
    assert "nmr.start_task" in action_keys


def test_registry_rejects_duplicate_device_key():
    """验证注册表不允许静默覆盖同键设备。"""
    registry = DeviceRegistry()
    first_device = build_nmr_device(sim_mode=True)
    second_device = build_nmr_device(sim_mode=False)

    registry.register(first_device)

    with pytest.raises(ValueError, match="nmr_2278"):
        registry.register(second_device)


def test_build_device_returns_registered_category_device():
    """验证设备工厂能够按类别构建设备。"""
    device = build_device("nmr", sim_mode=False)

    assert device.key == "nmr_2278"
    assert device.category == "核磁共振仪"
    assert device.device_type == "NMRSpectrometer"
    assert device.sim_mode is False


def test_list_supported_categories_contains_expected_entries():
    """验证工厂暴露支持的设备类别。"""
    categories = list_supported_categories()

    assert "nmr" in categories
    assert "gpc" in categories
    assert "resin" in categories
    assert "pi" in categories
    assert "station" in categories


def test_execute_action_calls_action_executor():
    """验证设备动作执行入口返回执行器结果。"""
    device = build_nmr_device(sim_mode=True)

    result = device.execute_action(
        "nmr.start_task",
        {"task_code": "task-001"},
        {},
    )

    assert result == {"status": "submitted", "task_code": "task-001"}
