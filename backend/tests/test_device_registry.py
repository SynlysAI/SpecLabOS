"""设备注册表测试。"""

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
