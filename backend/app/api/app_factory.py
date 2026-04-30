"""FastAPI 应用工厂。"""

from collections.abc import Callable

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import devices, logs, workflows
from app.core.config import Settings, get_settings
from app.runtime import get_workflow_dispatcher


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
    application.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://127.0.0.1:5173",
            "http://localhost:5173",
            "http://[::1]:5173",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    application.include_router(devices.router)
    application.include_router(devices.device_images_router)
    application.include_router(workflows.router)
    application.include_router(workflows.workflow_runs_router)
    application.include_router(logs.router)

    @application.on_event("startup")
    def _start_workflow_dispatcher() -> None:
        """启动工作流后台调度器。"""
        get_workflow_dispatcher().start()

    @application.on_event("shutdown")
    def _stop_workflow_dispatcher() -> None:
        """停止工作流后台调度器。"""
        get_workflow_dispatcher().stop()

    return application
