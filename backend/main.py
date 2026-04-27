"""后端应用入口。"""

from fastapi import FastAPI

from app.core.config import get_settings


def create_app() -> FastAPI:
    """创建并返回 FastAPI 应用实例。"""
    settings = get_settings()
    application = FastAPI(title=settings.app.name)
    return application


app = create_app()
