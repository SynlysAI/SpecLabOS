"""MongoDB 数据库访问入口。"""

from functools import lru_cache

from pymongo import MongoClient
from pymongo.database import Database

from app.core.config import get_settings


@lru_cache(maxsize=1)
def get_mongo_client() -> MongoClient:
    """创建并缓存 MongoDB 客户端。"""
    settings = get_settings()
    return MongoClient(settings.mongo.uri)


def get_database() -> Database:
    """获取当前配置对应的 MongoDB 数据库实例。"""
    settings = get_settings()
    return get_mongo_client()[settings.mongo.database]
