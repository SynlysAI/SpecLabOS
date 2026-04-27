"""后端应用入口。"""

from fastapi import FastAPI

from app.api.app_factory import create_app as build_app
from app.core.config import get_settings


def create_app() -> FastAPI:
    """创建并返回后端应用实例。"""
    return build_app(settings_factory=get_settings)


app = create_app()
