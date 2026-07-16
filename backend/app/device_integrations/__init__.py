"""设备集成插件扫描入口。"""

import importlib.util
from pathlib import Path
from types import ModuleType
from typing import Any

import yaml

from app.core.config import DeviceItemSettings, get_settings
from app.devices.registry import register_device
from app.domain.device import DeviceResource

_INTEGRATION_ROOT = Path(__file__).resolve().parent


def load_device_integrations() -> None:
    """扫描并加载设备集成目录。"""
    for integration_dir in _iter_integration_dirs():
        _load_integration_config(integration_dir)
        _load_integration_capabilities(integration_dir)


def _iter_integration_dirs() -> list[Path]:
    """遍历设备集成目录。

    Returns:
        包含 device.yaml 或 capabilities.py 的集成目录列表。
    """
    if not _INTEGRATION_ROOT.is_dir():
        return []
    return sorted(
        path for path in _INTEGRATION_ROOT.iterdir()
        if path.is_dir()
        and not path.name.startswith("_")
        and (
            (path / "device.yaml").is_file()
            or (path / "capabilities.py").is_file()
        )
    )


def _load_integration_config(integration_dir: Path) -> None:
    """加载单个集成目录中的设备定义。

    Args:
        integration_dir: 设备集成目录。
    """
    config_file = integration_dir / "device.yaml"
    if not config_file.is_file():
        return
    raw_config = yaml.safe_load(config_file.read_text(encoding="utf-8"))
    if not isinstance(raw_config, dict):
        return

    device_type = str(raw_config.get("device_type") or "")
    category = str(raw_config.get("category") or "")
    adapter_type = raw_config.get("adapter_type")
    capabilities = raw_config.get("capabilities") or []
    instances = raw_config.get("instances") or {}
    if not isinstance(instances, dict):
        return

    for device_id, instance_config in instances.items():
        if not isinstance(instance_config, dict):
            continue
        register_device(_build_device_resource(
            str(device_id),
            instance_config,
            device_type,
            category,
            adapter_type,
            capabilities,
        ))
        _register_instance_settings(str(device_id), instance_config)


def _register_instance_settings(
    device_id: str,
    instance_config: dict[str, Any],
) -> None:
    """注册设备实例运行配置。

    Args:
        device_id: 设备标识。
        instance_config: 单台设备配置。
    """
    settings = get_settings()
    if device_id in settings.devices.items:
        return
    settings.devices.items[device_id] = DeviceItemSettings(
        enabled=instance_config.get("enabled"),
        image=str(instance_config.get("image") or ""),
        endpoints=dict(instance_config.get("endpoints") or {}),
        status_endpoints=list(instance_config.get("status_endpoints") or []),
        health_path=str(instance_config.get("health_path") or ""),
        health_device=str(instance_config.get("health_device") or ""),
    )


def _build_device_resource(
    device_id: str,
    instance_config: dict[str, Any],
    device_type: str,
    category: str,
    adapter_type: str | None,
    capabilities: list[str],
) -> DeviceResource:
    """构建设备资源实例。

    Args:
        device_id: 设备标识。
        instance_config: 单台设备配置。
        device_type: 默认设备类型。
        category: 默认设备分类。
        adapter_type: 默认适配器类型。
        capabilities: 默认能力列表。

    Returns:
        设备资源实例。
    """
    return DeviceResource(
        device_id=device_id,
        name=str(instance_config.get("name") or device_id),
        category=str(instance_config.get("category") or category),
        device_type=str(instance_config.get("device_type") or device_type),
        location=str(instance_config.get("location") or ""),
        enabled=bool(instance_config.get("enabled", True)),
        sim_mode=bool(instance_config.get("sim_mode", True)),
        adapter_type=instance_config.get("adapter_type") or adapter_type,
        capabilities=list(instance_config.get("capabilities") or capabilities),
    )


def _load_integration_capabilities(integration_dir: Path) -> ModuleType | None:
    """加载单个集成目录中的能力实现模块。

    Args:
        integration_dir: 设备集成目录。

    Returns:
        已加载的能力模块，不存在时返回 None。
    """
    capabilities_file = integration_dir / "capabilities.py"
    if not capabilities_file.is_file():
        return None
    module_name = f"app.device_integrations.{integration_dir.name}.capabilities"
    spec = importlib.util.spec_from_file_location(module_name, capabilities_file)
    if spec is None or spec.loader is None:
        return None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
