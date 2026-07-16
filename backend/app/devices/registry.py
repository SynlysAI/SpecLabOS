"""设备、能力、适配器与本地执行器注册表。"""

from collections.abc import Callable
from typing import Any, Type

from app.domain.adapter import ExecutionAdapter
from app.domain.capability import DeviceCapability
from app.domain.device import DeviceResource


CapabilityExecutor = Callable[[dict[str, Any], dict[str, Any]], dict[str, Any]]

_DEVICE_REGISTRY: dict[str, DeviceResource] = {}
_CAPABILITY_REGISTRY: dict[str, DeviceCapability] = {}
_ADAPTER_REGISTRY: dict[str, Type[ExecutionAdapter]] = {}
_EXECUTOR_REGISTRY: dict[tuple[str, str], CapabilityExecutor] = {}


def device(cls):
    """类装饰器：自动注册设备资源。"""
    instance = cls()
    _DEVICE_REGISTRY[instance.device_id] = instance
    return cls


def register_device(device_resource: DeviceResource) -> None:
    """注册设备资源实例。

    Args:
        device_resource: 待注册的设备资源。
    """
    _DEVICE_REGISTRY[device_resource.device_id] = device_resource


def capability(device_category: str):
    """函数装饰器：自动注册设备能力声明。

    Args:
        device_category: 能力所属设备类别。

    Returns:
        能力声明函数装饰器。
    """
    def decorator(fn):
        cap = fn()
        _CAPABILITY_REGISTRY[cap.capability_key] = cap
        return fn
    return decorator


def adapter(adapter_type: str):
    """类装饰器：自动注册执行适配器。

    Args:
        adapter_type: 适配器类型。

    Returns:
        适配器类装饰器。
    """
    def decorator(cls):
        _ADAPTER_REGISTRY[adapter_type] = cls
        return cls
    return decorator


def local_executor(device_id: str, capability_key: str):
    """函数装饰器：注册本地能力执行器。

    Args:
        device_id: 设备标识。
        capability_key: 能力标识。

    Returns:
        本地执行器函数装饰器。
    """
    def decorator(fn: CapabilityExecutor):
        _EXECUTOR_REGISTRY[(device_id, capability_key)] = fn
        return fn
    return decorator


def register_local_executor(
    device_id: str,
    capability_key: str,
    executor: CapabilityExecutor,
) -> None:
    """注册本地能力执行器。

    Args:
        device_id: 设备标识。
        capability_key: 能力标识。
        executor: 执行函数。
    """
    _EXECUTOR_REGISTRY[(device_id, capability_key)] = executor


def get_device(device_id: str) -> DeviceResource | None:
    """获取已注册设备资源。

    Args:
        device_id: 设备标识。

    Returns:
        设备资源，不存在时返回 None。
    """
    return _DEVICE_REGISTRY.get(device_id)


def list_devices() -> list[DeviceResource]:
    """列出所有已注册设备资源。"""
    return list(_DEVICE_REGISTRY.values())


def get_capability(capability_key: str) -> DeviceCapability | None:
    """获取已注册能力声明。

    Args:
        capability_key: 能力标识。

    Returns:
        能力声明，不存在时返回 None。
    """
    return _CAPABILITY_REGISTRY.get(capability_key)


def list_capabilities() -> list[DeviceCapability]:
    """列出所有已注册能力声明。"""
    return list(_CAPABILITY_REGISTRY.values())


def list_capabilities_by_category(device_category: str) -> list[DeviceCapability]:
    """列出指定设备类别支持的能力。

    Args:
        device_category: 设备类别。

    Returns:
        能力声明列表。
    """
    return [
        cap for cap in _CAPABILITY_REGISTRY.values()
        if cap.device_category == device_category
    ]


def get_adapter_class(adapter_type: str) -> Type[ExecutionAdapter] | None:
    """获取已注册适配器类。

    Args:
        adapter_type: 适配器类型。

    Returns:
        适配器类，不存在时返回 None。
    """
    return _ADAPTER_REGISTRY.get(adapter_type)


def list_adapter_types() -> list[str]:
    """列出所有已注册适配器类型。"""
    return list(_ADAPTER_REGISTRY.keys())


def get_local_executor(
    device_id: str,
    capability_key: str,
) -> CapabilityExecutor | None:
    """获取本地能力执行器。

    Args:
        device_id: 设备标识。
        capability_key: 能力标识。

    Returns:
        本地执行器，不存在时返回 None。
    """
    return _EXECUTOR_REGISTRY.get((device_id, capability_key))


def list_local_executor_keys() -> list[tuple[str, str]]:
    """列出所有本地执行器键。"""
    return list(_EXECUTOR_REGISTRY.keys())
