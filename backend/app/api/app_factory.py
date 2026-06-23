"""FastAPI 应用工厂。"""

from collections.abc import Callable
from pathlib import Path

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response as StarletteResponse

from app.api.routes import auth, devices, logs, smartaccess, tools, workflows
from app.core.config import Settings, get_settings
from app.runtime import get_workflow_dispatcher

_FRONTEND_DIST = Path(__file__).resolve().parent.parent.parent.parent / "frontend" / "dist"


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
    application.include_router(auth.router)
    application.include_router(devices.router)
    application.include_router(devices.device_images_router)
    application.include_router(smartaccess.router)
    application.include_router(workflows.router)
    application.include_router(workflows.workflow_runs_router)
    application.include_router(logs.router)
    application.include_router(tools.router)

    @application.on_event("startup")
    def _start_workflow_dispatcher() -> None:
        """启动工作流后台调度器。"""
        get_workflow_dispatcher().start()

    @application.on_event("shutdown")
    def _stop_workflow_dispatcher() -> None:
        """停止工作流后台调度器。"""
        get_workflow_dispatcher().stop()

    # 生产模式：托管前端静态文件
    if _FRONTEND_DIST.is_dir():
        application.add_middleware(
            _NoCacheMiddleware,
            static_path=str(_FRONTEND_DIST),
        )
        application.mount(
            "/", _SPAStaticFiles(directory=str(_FRONTEND_DIST), html=True), name="frontend"
        )

    return application


class _NoCacheMiddleware(BaseHTTPMiddleware):
    """为前端静态文件添加禁用缓存的响应头。"""

    def __init__(self, app, static_path: str) -> None:
        super().__init__(app)
        self._static_path = static_path

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        # 仅对 index.html 禁用缓存，带 hash 的 JS/CSS 资源应长期缓存
        if request.url.path in ("", "/") or request.url.path.endswith(".html"):
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
        return response


class _SPAStaticFiles(StaticFiles):
    """支持 SPA 路由回退的静态文件服务。"""

    async def get_response(self, path: str, scope) -> StarletteResponse:
        """获取静态资源响应，找不到文件时回退到 index.html。

        Args:
            path: 去掉前导斜杠后的请求路径。
            scope: ASGI 请求作用域。

        Returns:
            静态资源响应或 index.html 回退响应。
        """
        response = None
        try:
            response = await super().get_response(path, scope)
        except StarletteHTTPException as exc:
            if exc.status_code != 404:
                raise

        if response is not None and response.status_code != 404:
            return response

        # 带文件扩展名的请求不回退，直接返回 404
        if "." in path.rsplit("/", maxsplit=1)[-1]:
            raise StarletteHTTPException(status_code=404)

        return await super().get_response("index.html", scope)
