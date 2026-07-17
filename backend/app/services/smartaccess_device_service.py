"""SmartAccess 虚拟设备服务。"""

from datetime import datetime
from typing import Any

from pymongo.errors import PyMongoError

from app.domain.capability import DeviceCapability
from app.domain.device import DeviceResource
from app.services.smartaccess_node_service import SmartAccessNodeService
from app.services.smartaccess_service import SmartAccessService


ACTIVE_RUN_STATUSES = {"queued", "accepted", "running"}
ERROR_RUN_STATUSES = {"failed", "blocked", "rejected", "cancelled"}


class SmartAccessDeviceService:
    """从 SmartAccess 模板和运行记录生成虚拟设备资源。"""

    def __init__(
        self,
        smartaccess_service: SmartAccessService,
        node_service: SmartAccessNodeService | None = None,
    ) -> None:
        """初始化 SmartAccess 虚拟设备服务。

        Args:
            smartaccess_service: SmartAccess 服务。
            node_service: SmartAccess 节点心跳服务,用于推断执行端在线状态。
        """
        self._smartaccess_service = smartaccess_service
        self._node_service = node_service

    def list_devices(self) -> list[DeviceResource]:
        """列出 SmartAccess 虚拟设备。

        Returns:
            SmartAccess 虚拟设备资源列表。
        """
        try:
            templates = self._smartaccess_service.list_templates(status="published")
        except PyMongoError:
            return []
        except Exception:
            return []

        try:
            runs = self._smartaccess_service.list_runs()
        except PyMongoError:
            runs = []
        except Exception:
            runs = []

        node_status_map = self._build_node_status_map()

        device_map: dict[str, DeviceResource] = {}
        for template in templates:
            device_id = self._extract_template_device_id(template)
            if not device_id:
                continue
            resource = device_map.setdefault(
                device_id,
                self._build_device_resource(device_id, template),
            )
            capability_key = self._build_capability_key(template)
            if capability_key and capability_key not in resource.capabilities:
                resource.capabilities.append(capability_key)

        for resource in device_map.values():
            self._apply_template_status(resource)

        for run in runs:
            device_id = run.get("target_device_id") or run.get("smartaccess_node_id")
            if not device_id:
                continue
            resource = device_map.get(device_id)
            if resource is None:
                continue
            self._apply_run_status(resource, run)

        for resource in device_map.values():
            self._apply_node_status(resource, node_status_map)

        return list(device_map.values())

    def list_actions(self, device_key: str) -> list[DeviceCapability]:
        """列出 SmartAccess 虚拟设备可执行的已发布工作流。

        Args:
            device_key: SmartAccess 虚拟设备标识。

        Returns:
            由 SmartAccess 已发布模板转换得到的设备能力列表。
        """
        device_id = self._strip_virtual_device_prefix(device_key)
        try:
            templates = self._smartaccess_service.list_templates(status="published")
        except PyMongoError:
            return []
        except Exception:
            return []

        return [
            self._build_capability(template)
            for template in templates
            if self._extract_template_device_id(template) == device_id
            and self._build_capability_key(template)
        ]

    @staticmethod
    def _extract_template_device_id(template: dict[str, Any]) -> str:
        """从模板记录中提取设备标识。

        Args:
            template: SmartAccess 模板记录。

        Returns:
            设备标识。
        """
        return (
            template.get("source_device_id")
            or template.get("anchor_profile")
            or template.get("template_id")
            or ""
        )

    @staticmethod
    def _build_device_resource(
        device_id: str,
        source: dict[str, Any],
    ) -> DeviceResource:
        """构造 SmartAccess 虚拟设备资源。

        Args:
            device_id: 设备标识。
            source: 来源记录。

        Returns:
            设备资源。
        """
        display_name = source.get("target_device_id") or source.get("name") or device_id
        return DeviceResource(
            device_id=f"smartaccess:{device_id}",
            name=f"SmartAccess - {display_name}",
            category="SmartAccess 远程设备",
            device_type="SmartAccessDevice",
            location=source.get("smartaccess_node_id") or source.get("anchor_profile") or "远程",
            enabled=True,
            sim_mode=False,
            adapter_type="smartaccess",
            connection_status="unknown",
            execution_status="idle",
            data_status="unknown",
            maintenance_status="available",
            status_sources=["smartaccess", "published_workflow"],
            status_message="SmartAccess 已发布工作流可用,等待执行端心跳",
        )

    @staticmethod
    def _build_capability(template: dict[str, Any]) -> DeviceCapability:
        """将 SmartAccess 模板转换为设备能力。

        Args:
            template: SmartAccess 模板记录。

        Returns:
            设备能力声明。
        """
        template_id = template.get("template_id", "")
        template_version = template.get("template_version", "")
        step_count = int(template.get("step_count") or 0)
        return DeviceCapability(
            capability_key=f"smartaccess/{template_id}/{template_version}",
            device_category="SmartAccess 远程设备",
            name=template.get("name") or template.get("workflow_id") or template_id,
            description=(
                f"SmartAccess 已发布工作流，版本 {template_version}，"
                f"共 {step_count} 个步骤"
            ),
            step_mode="single_step",
            parameter_schema={
                "type": "object",
                "properties": {
                    "smartaccess_node_id": {
                        "type": "string",
                        "description": "SmartAccess 节点 ID；为空时使用模板锚点或设备标识",
                    },
                    "target_device_id": {
                        "type": "string",
                        "description": "SmartAccess 目标设备 ID；为空时使用当前虚拟设备标识",
                    },
                    "requested_by": {
                        "type": "string",
                        "description": "发起人，默认 system",
                    },
                },
            },
            result_schema={
                "type": "object",
                "properties": {
                    "run_id": {"type": "string"},
                    "status": {"type": "string"},
                },
            },
        )

    @staticmethod
    def _build_capability_key(template: dict[str, Any]) -> str:
        """构造 SmartAccess 模板能力标识。

        Args:
            template: SmartAccess 模板记录。

        Returns:
            能力标识。
        """
        template_id = template.get("template_id", "")
        template_version = template.get("template_version", "")
        if not template_id or not template_version:
            return ""
        return f"smartaccess/{template_id}/{template_version}"

    @staticmethod
    def _strip_virtual_device_prefix(device_key: str) -> str:
        """去除 SmartAccess 虚拟设备前缀。

        Args:
            device_key: 设备标识。

        Returns:
            原始 SmartAccess 设备标识。
        """
        prefix = "smartaccess:"
        if device_key.startswith(prefix):
            return device_key[len(prefix):]
        return device_key

    @staticmethod
    def _apply_template_status(resource: DeviceResource) -> None:
        """根据已发布模板设置虚拟设备可用状态。

        注意: ``connection_status`` 由 ``_apply_node_status`` 统一按心跳注入,
        此处不再硬编码 online。

        Args:
            resource: SmartAccess 虚拟设备资源。
        """
        workflow_count = len(resource.capabilities)
        resource.status_updated_at = datetime.now()
        resource.execution_status = "idle"
        resource.status_sources = ["smartaccess", "published_workflow"]
        resource.status_message = (
            f"已发布 SmartAccess 工作流 {workflow_count} 个"
        )

    @staticmethod
    def _apply_run_status(resource: DeviceResource, run: dict[str, Any]) -> None:
        """根据最近运行记录推断虚拟设备执行状态。

        注意: ``connection_status`` 由 ``_apply_node_status`` 统一按心跳注入,
        此处仅推断 ``execution_status``。

        Args:
            resource: 设备资源。
            run: SmartAccess 运行记录。
        """
        status = run.get("status", "queued")
        resource.status_updated_at = datetime.now()
        resource.status_sources = ["smartaccess", "run_record"]
        if status in ACTIVE_RUN_STATUSES:
            resource.execution_status = "running" if status == "running" else "idle"
            resource.status_message = f"最近 SmartAccess 运行状态: {status}"
            return
        if status in ERROR_RUN_STATUSES:
            resource.execution_status = "error"
            resource.status_message = f"最近 SmartAccess 运行异常: {status}"
            return
        if status == "success":
            resource.execution_status = "idle"
            resource.status_message = "最近 SmartAccess 运行成功"

    def _build_node_status_map(self) -> dict[str, str]:
        """构建节点 ID 到在线状态的映射。

        Returns:
            ``{node_id: "online" | "offline"}``;节点服务不可用时返回空字典。
        """
        if self._node_service is None:
            return {}
        try:
            nodes = self._node_service.list_nodes()
        except Exception:  # noqa: BLE001 - 节点查询失败不应阻断设备列表
            return {}
        return {item.get("node_id", ""): item.get("status", "offline") for item in nodes}

    @staticmethod
    def _apply_node_status(
        resource: DeviceResource,
        node_status_map: dict[str, str],
    ) -> None:
        """根据执行端心跳状态注入 ``connection_status``。

        Args:
            resource: SmartAccess 虚拟设备资源。
            node_status_map: 节点 ID 到在线状态的映射。
        """
        prefix = "smartaccess:"
        node_id = (
            resource.device_id[len(prefix):]
            if resource.device_id.startswith(prefix)
            else resource.device_id
        )
        node_status = node_status_map.get(node_id)
        resource.status_updated_at = datetime.now()
        if node_status == "online":
            resource.connection_status = "online"
            if "node_heartbeat" not in resource.status_sources:
                resource.status_sources.append("node_heartbeat")
            resource.status_message = (
                f"{resource.status_message};执行端心跳正常"
            )
            return
        if node_status == "offline":
            resource.connection_status = "offline"
            resource.execution_status = "idle"
            if "node_heartbeat" not in resource.status_sources:
                resource.status_sources.append("node_heartbeat")
            resource.status_message = "SmartAccess 执行端离线"
            return
        resource.connection_status = "unknown"
        resource.status_message = (
            f"{resource.status_message};执行端未上报心跳"
        )
