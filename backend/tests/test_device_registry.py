"""设备注册表测试。"""

from app.devices import load_builtin_devices
from app.devices.registry import (
    get_capability,
    get_device,
    get_local_executor,
    list_capabilities,
    list_devices,
    list_local_executor_keys,
)


def test_builtin_devices_register_resources_and_capabilities():
    """验证内置设备模块会注册设备资源与能力声明。"""
    load_builtin_devices()

    device = get_device("nmr_2278")
    capability = get_capability("nmr.start_task")

    assert device is not None
    assert device.device_id == "nmr_2278"
    assert device.device_type == "NMRSpectrometer"
    assert capability is not None
    assert capability.name == "开始任务"


def test_builtin_registry_counts_are_complete():
    """验证内置设备、能力和本地执行器注册数量完整。"""
    load_builtin_devices()

    assert len(list_devices()) == 12
    assert len(list_capabilities()) == 39
    assert len(list_local_executor_keys()) == 47


def test_local_executor_registered_for_lcms_action():
    """验证 LCMS 能力已注册本地执行器。"""
    load_builtin_devices()

    executor = get_local_executor("lcms_2278", "lcms.check_status")

    assert executor is not None
    assert executor({"sample": "s-1"}, {"run_id": "run-1"}) == {
        "device": "lcms_2278",
        "action": "check_status",
        "status": "completed",
        "response": {"sample": "s-1"},
    }
