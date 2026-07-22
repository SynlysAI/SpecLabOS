"""应用运行时共享对象。"""

from functools import lru_cache

import pika

from app.adapters.adapter_service import AdapterService
from app.core.config import get_settings
from app.core.mongo import get_database
from app.devices import load_builtin_devices
from app.repositories.device_permission_repository import (
    DevicePermissionRepository,
)
from app.repositories.event_repository import EventRepository
from app.repositories.external_experiment_dispatch_repository import (
    ExternalExperimentDispatchRepository,
)
from app.repositories.smartaccess_node_repository import (
    SmartAccessNodeRepository,
)
from app.repositories.smartaccess_repository import SmartAccessRepository
from app.repositories.workflow_repository import WorkflowRepository
from app.runners.device_lock_manager import DeviceLockManager
from app.runners.smartaccess_node_sweeper import SmartAccessNodeSweeper
from app.runners.smartaccess_run_sweeper import SmartAccessRunSweeper
from app.runners.workflow_dispatcher import WorkflowDispatcher
from app.runners.workflow_runner import WorkflowRunner
from app.services.device_permission_service import DevicePermissionService
from app.services.device_service import DeviceService
from app.services.device_status_service import DeviceStatusService
from app.services.event_bus import EventBus
from app.services.external_experiment_dispatch_service import (
    ExternalExperimentDispatchService,
)
from app.services.smartaccess_mq import (
    SmartAccessNullPublisher,
    SmartAccessRabbitMQPublisher,
)
from app.services.smartaccess_device_service import SmartAccessDeviceService
from app.services.smartaccess_node_service import SmartAccessNodeService
from app.services.smartaccess_service import SmartAccessService


@lru_cache(maxsize=1)
def ensure_device_registry_loaded() -> bool:
    """加载并缓存内置设备注册信息。"""
    load_builtin_devices()
    return True


@lru_cache(maxsize=1)
def get_device_service() -> DeviceService:
    """构建并缓存全局设备服务。"""
    ensure_device_registry_loaded()
    return DeviceService(get_smartaccess_device_service())


@lru_cache(maxsize=1)
def get_device_status_service() -> DeviceStatusService:
    """构建并缓存全局设备状态服务。"""
    ensure_device_registry_loaded()
    return DeviceStatusService()


@lru_cache(maxsize=1)
def get_smartaccess_device_service() -> SmartAccessDeviceService:
    """构建并缓存 SmartAccess 虚拟设备服务。"""
    return SmartAccessDeviceService(
        smartaccess_service=get_smartaccess_service(),
        node_service=get_smartaccess_node_service(),
    )


@lru_cache(maxsize=1)
def get_workflow_repository() -> WorkflowRepository:
    """构建并缓存全局工作流仓储。"""
    return WorkflowRepository(get_database())


@lru_cache(maxsize=1)
def get_smartaccess_repository() -> SmartAccessRepository:
    """构建并缓存 SmartAccess 仓储。"""
    return SmartAccessRepository(get_database())


@lru_cache(maxsize=1)
def get_external_experiment_dispatch_repository() -> ExternalExperimentDispatchRepository:
    """构建并缓存外部实验任务仓储。"""
    return ExternalExperimentDispatchRepository(get_database())


@lru_cache(maxsize=1)
def get_external_experiment_dispatch_service() -> ExternalExperimentDispatchService:
    """构建并缓存外部实验任务服务。"""
    return ExternalExperimentDispatchService(
        repository=get_external_experiment_dispatch_repository(),
    )


@lru_cache(maxsize=1)
def get_smartaccess_publisher():
    """构建并缓存 SmartAccess MQ 发布器。

    当 RabbitMQ 未配置或连接失败时返回空发布器，避免启动崩溃。
    """
    settings = get_settings()

    def _channel():
        """创建 RabbitMQ channel。"""
        credentials = pika.PlainCredentials(
            settings.rabbitmq.username,
            settings.rabbitmq.password,
        )
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host=settings.rabbitmq.host,
                port=settings.rabbitmq.port,
                credentials=credentials,
            )
        )
        return connection.channel()

    try:
        _channel().close()
    except Exception:
        import logging
        logging.getLogger(__name__).warning(
            "RabbitMQ 连接失败，SmartAccess 远程任务下发不可用，已回退空发布器"
        )
        return SmartAccessNullPublisher()
    return SmartAccessRabbitMQPublisher(channel_factory=_channel)


@lru_cache(maxsize=1)
def get_smartaccess_service() -> SmartAccessService:
    """构建并缓存 SmartAccess 服务。"""
    return SmartAccessService(
        repository=get_smartaccess_repository(),
        publisher=get_smartaccess_publisher(),
    )


@lru_cache(maxsize=1)
def get_smartaccess_run_sweeper() -> SmartAccessRunSweeper:
    """构建并缓存 SmartAccess 超时扫描器。"""
    return SmartAccessRunSweeper(get_smartaccess_service())


@lru_cache(maxsize=1)
def get_smartaccess_node_repository() -> SmartAccessNodeRepository:
    """构建并缓存 SmartAccess 节点心跳仓储。"""
    return SmartAccessNodeRepository(get_database())


@lru_cache(maxsize=1)
def get_smartaccess_node_service() -> SmartAccessNodeService:
    """构建并缓存 SmartAccess 节点心跳服务。"""
    return SmartAccessNodeService(get_smartaccess_node_repository())


@lru_cache(maxsize=1)
def get_smartaccess_node_sweeper() -> SmartAccessNodeSweeper:
    """构建并缓存 SmartAccess 节点心跳扫描器。"""
    return SmartAccessNodeSweeper(get_smartaccess_node_service())


@lru_cache(maxsize=1)
def get_lock_manager() -> DeviceLockManager:
    """构建并缓存全局设备锁管理器。"""
    return DeviceLockManager()


@lru_cache(maxsize=1)
def get_event_repository() -> EventRepository:
    """构建并缓存全局事件仓储。"""
    return EventRepository()


@lru_cache(maxsize=1)
def get_event_bus() -> EventBus:
    """构建并缓存全局事件总线。"""
    return EventBus(get_event_repository())


@lru_cache(maxsize=1)
def get_adapter_service() -> AdapterService:
    """构建并缓存全局适配器服务。"""
    ensure_device_registry_loaded()
    return AdapterService(get_event_bus())


@lru_cache(maxsize=1)
def get_workflow_runner() -> WorkflowRunner:
    """构建并缓存全局工作流运行器。"""
    ensure_device_registry_loaded()
    return WorkflowRunner(
        lock_manager=get_lock_manager(),
        adapter_service=get_adapter_service(),
        event_bus=get_event_bus(),
    )


@lru_cache(maxsize=1)
def get_workflow_dispatcher() -> WorkflowDispatcher:
    """构建并缓存全局工作流调度器。"""
    return WorkflowDispatcher(
        workflow_repository=get_workflow_repository(),
        workflow_runner=get_workflow_runner(),
        lock_manager=get_lock_manager(),
    )


@lru_cache(maxsize=1)
def get_device_permission_repository() -> DevicePermissionRepository:
    """构建并缓存全局设备权限仓储。"""
    return DevicePermissionRepository(get_database())


@lru_cache(maxsize=1)
def get_device_permission_service() -> DevicePermissionService:
    """构建并缓存全局设备权限服务。"""
    return DevicePermissionService(
        repository=get_device_permission_repository(),
    )
