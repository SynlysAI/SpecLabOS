"""FastAPI 应用工厂。"""

from collections.abc import Callable

from fastapi import FastAPI

from app.api.routes import devices, logs, workflows
from app.core.config import Settings, get_settings


def create_app(
    settings_factory: Callable[[], Settings] = get_settings,
) -> FastAPI:
    """创建并组装 FastAPI 应用实例。

    Args:
        settings_factory: 返回系统配置的工厂函数。

    Returns:
        已挂载基础路由的 FastAPI 应用实例。
    """
    settings = settings_factory()
    application = FastAPI(title=settings.app.name)
    application.include_router(devices.router)
    application.include_router(devices.device_images_router)
    application.include_router(workflows.router)
    application.include_router(workflows.workflow_runs_router)
    application.include_router(logs.router)
    return application
