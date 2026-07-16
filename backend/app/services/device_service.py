"""设备服务。"""

from datetime import datetime
from typing import Any

from app.core.config import get_settings
from app.devices.registry import (
    get_device,
    list_capabilities_by_category,
    list_devices,
)
from app.domain.capability import DeviceCapability
from app.domain.device import DeviceResource
from app.services.smartaccess_device_service import SmartAccessDeviceService


DEVICE_DISPLAY_ORDER = {
    "nmr_2278": 0,
    "pi_2278": 1,
    "gpc_2278": 2,
    "ir_2278": 3,
    "raman_2278": 4,
    "lcms_2278": 5,
    "resin_2278": 6,
    "resin_2278_2": 7,
    "resin_1438": 8,
    "metal_108": 9,
    "cat_108": 10,
    "micro_108": 11,
}


class DeviceService:
    """封装新设备资源与能力查询能力。"""

    def __init__(
        self,
        smartaccess_device_service: SmartAccessDeviceService | None = None,
    ) -> None:
        """初始化设备服务。

        Args:
            smartaccess_device_service: SmartAccess 虚拟设备服务。
        """
        self._smartaccess_device_service = smartaccess_device_service

    def get_device(self, device_key: str) -> DeviceResource | None:
        """获取指定设备资源。

        Args:
            device_key: 设备唯一标识。

        Returns:
            设备资源，不存在时返回 None。
        """
        device = get_device(device_key)
        if device is None:
            device = self._get_smartaccess_device(device_key)
        if device is not None:
            self._apply_enabled_config([device])
        return device

    def list_devices(self, include_smartaccess: bool = True) -> list[DeviceResource]:
        """列出所有已注册设备资源。

        Args:
            include_smartaccess: 是否包含 SmartAccess 虚拟设备。
        """
        devices = [*list_devices()]
        if include_smartaccess:
            devices.extend(self._list_smartaccess_devices())
        self._apply_enabled_config(devices)
        return sorted(
            devices,
            key=lambda device: DEVICE_DISPLAY_ORDER.get(device.device_id, 999),
        )

    def list_actions(self, device_key: str) -> list[DeviceCapability]:
        """列出指定设备支持的能力。

        Args:
            device_key: 设备唯一标识。

        Returns:
            设备能力声明列表。
        """
        device = self.get_device(device_key)
        if device is None:
            return []
        if device.adapter_type == "smartaccess":
            return self._list_smartaccess_actions(device_key)
        if device.capabilities:
            return [
                cap for cap in list_capabilities_by_category(device.category)
                if cap.capability_key in device.capabilities
                and cap.step_mode != "hidden"
            ]
        return [
            cap for cap in list_capabilities_by_category(device.category)
            if cap.step_mode != "hidden"
        ]

    @staticmethod
    def serialize_device(device: DeviceResource) -> dict:
        """将设备资源转换为前端可直接消费的字典。

        Args:
            device: 设备资源。

        Returns:
            前端设备字典。
        """
        updated_at = DeviceService._format_updated_at(device)
        state = DeviceService._status_to_state(device)
        item = {
            "key": device.device_id,
            "name": device.name,
            "category": device.category,
            "device_type": device.device_type or device.category,
            "enabled": device.enabled,
            "sim_mode": device.sim_mode,
            "location": device.location,
            "connection": device.connection,
            "adapter_type": device.adapter_type or "",
            "status_snapshot": {
                "state": state,
                "message": device.status_message or (
                    f"连接：{device.connection_status}，执行：{device.execution_status}"
                ),
                "updated_at": updated_at,
            },
        }
        image_url = DeviceService._get_config_image_url(device.device_id)
        if image_url:
            item["image_url"] = image_url
        return item

    @staticmethod
    def serialize_action(capability: DeviceCapability) -> dict:
        """将能力声明转换为旧动作响应字典。

        Args:
            capability: 设备能力声明。

        Returns:
            前端动作字典。
        """
        return {
            "action_key": capability.capability_key,
            "name": capability.name,
            "description": capability.description,
            "step_mode": capability.step_mode,
            "parameter_schema": DeviceService._schema_to_fields(
                capability.parameter_schema
            ),
        }

    @staticmethod
    def _format_updated_at(device: DeviceResource) -> str:
        """格式化状态更新时间。

        Args:
            device: 设备资源。

        Returns:
            前端展示时间。
        """
        if device.status_updated_at is None:
            return datetime.now().strftime("%Y-%m-%d %H:%M")
        return device.status_updated_at.strftime("%Y-%m-%d %H:%M")

    @staticmethod
    def _schema_to_fields(schema: dict[str, Any]) -> list[dict[str, Any]]:
        """将 JSON Schema 转换为前端旧字段列表。

        Args:
            schema: JSON Schema 参数声明。

        Returns:
            前端字段列表。
        """
        properties = schema.get("properties", {}) if schema else {}
        required_fields = set(schema.get("required", [])) if schema else set()
        fields = []
        for name, field_schema in properties.items():
            fields.append({
                "name": name,
                "type": DeviceService._schema_type_to_field_type(
                    field_schema.get("type", "string")
                ),
                "required": name in required_fields,
                "description": field_schema.get("description", ""),
            })
        return fields

    @staticmethod
    def _schema_type_to_field_type(schema_type: str) -> str:
        """将 JSON Schema 类型转换为前端字段类型。

        Args:
            schema_type: JSON Schema 类型。

        Returns:
            前端字段类型。
        """
        if schema_type in {"array", "object"}:
            return "json"
        return schema_type

    @staticmethod
    def _apply_enabled_config(devices: list[DeviceResource]) -> None:
        """按配置应用设备启用状态。

        Args:
            devices: 待更新启用状态的设备列表。
        """
        device_settings = get_settings().devices
        disabled_keys = set(device_settings.disabled_keys)
        for device in devices:
            item_config = device_settings.items.get(device.device_id)
            if item_config is not None and item_config.enabled is not None:
                device.enabled = item_config.enabled
            else:
                device.enabled = device.device_id not in disabled_keys

    @staticmethod
    def _get_config_image_url(device_id: str) -> str:
        """获取配置中声明的设备图片地址。

        Args:
            device_id: 设备标识。

        Returns:
            设备图片访问路径，未配置时返回空字符串。
        """
        image_name = get_settings().devices.items.get(device_id)
        if image_name is None or not image_name.image:
            return ""
        return f"/api/device-images/{image_name.image}"

    @staticmethod
    def _status_to_state(device: DeviceResource) -> str:
        """将四维状态折叠为前端旧状态。

        Args:
            device: 设备资源。

        Returns:
            前端旧状态值。
        """
        if not device.enabled:
            return "disabled"
        if device.connection_status in {"offline", "error", "unknown"}:
            return device.connection_status
        if device.execution_status not in ("", "idle"):
            return device.execution_status
        if device.connection_status in ("connected", "online"):
            return "online"
        return device.connection_status or "unknown"

    def _list_smartaccess_devices(self) -> list[DeviceResource]:
        """列出 SmartAccess 虚拟设备。

        Returns:
            SmartAccess 虚拟设备资源列表。
        """
        if self._smartaccess_device_service is None:
            return []
        return self._smartaccess_device_service.list_devices()

    def _list_smartaccess_actions(self, device_key: str) -> list[DeviceCapability]:
        """列出 SmartAccess 虚拟设备动作。

        Args:
            device_key: 设备唯一标识。

        Returns:
            SmartAccess 已发布工作流动作列表。
        """
        if self._smartaccess_device_service is None:
            return []
        return self._smartaccess_device_service.list_actions(device_key)

    def _get_smartaccess_device(self, device_key: str) -> DeviceResource | None:
        """获取 SmartAccess 虚拟设备。

        Args:
            device_key: 设备唯一标识。

        Returns:
            SmartAccess 虚拟设备，不存在时返回 None。
        """
        for device in self._list_smartaccess_devices():
            if device.device_id == device_key:
                return device
        return None
