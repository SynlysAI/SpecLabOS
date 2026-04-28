"""MongoDB 数据库访问入口。"""

from functools import lru_cache

import mongomock
from pymongo import MongoClient
from pymongo.database import Database
from pymongo.errors import ServerSelectionTimeoutError

from app.core.config import get_settings


@lru_cache(maxsize=1)
def get_mongo_client() -> MongoClient:
    """创建并缓存 MongoDB 客户端。"""
    settings = get_settings()
    client = MongoClient(
        settings.mongo.uri,
        serverSelectionTimeoutMS=1000,
    )
    try:
        client.admin.command("ping")
        return client
    except ServerSelectionTimeoutError:
        return mongomock.MongoClient()


def get_database() -> Database:
    """获取当前配置对应的 MongoDB 数据库实例。"""
    settings = get_settings()
    return get_mongo_client()[settings.mongo.database]
