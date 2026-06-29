"""MongoDB 数据库访问入口。"""

import logging
from functools import lru_cache

import mongomock
from pymongo import MongoClient
from pymongo.database import Database
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

from app.core.config import get_settings

logger = logging.getLogger(__name__)

_MONGO_TIMEOUT_MS = 20000


@lru_cache(maxsize=1)
def get_mongo_client() -> MongoClient:
    """创建并缓存 MongoDB 客户端。

    Returns:
        已连接验证的 MongoDB 客户端，连接失败时回退到内存模拟客户端。
    """
    settings = get_settings()
    client = MongoClient(
        settings.mongo.uri,
        serverSelectionTimeoutMS=_MONGO_TIMEOUT_MS,
        connectTimeoutMS=_MONGO_TIMEOUT_MS,
        socketTimeoutMS=_MONGO_TIMEOUT_MS,
        heartbeatFrequencyMS=10000,
    )
    try:
        client.admin.command("ping")
        logger.info("MongoDB 连接成功")
        return client
    except ServerSelectionTimeoutError:
        logger.warning("MongoDB 不可用，回退到内存模拟数据库")
        return mongomock.MongoClient()


def reset_mongo_client() -> None:
    """清除缓存的 MongoDB 客户端，下次访问时重新创建连接。

    当 MongoDB 中途宕机恢复后，调用此函数可强制重建连接。
    """
    get_mongo_client.cache_clear()
    logger.info("MongoDB 客户端缓存已清除")


def get_database() -> Database:
    """获取当前配置对应的 MongoDB 数据库实例。

    Returns:
        MongoDB 数据库实例。
    """
    settings = get_settings()
    return get_mongo_client()[settings.mongo.database]


__all__ = [
    "get_database",
    "get_mongo_client",
    "reset_mongo_client",
    "ConnectionFailure",
    "ServerSelectionTimeoutError",
]
