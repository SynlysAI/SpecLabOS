"""speclabos_data 数据库访问入口。"""

from functools import lru_cache

from pymongo.database import Database

from app.core.config import get_settings
from app.core.mongo import get_mongo_client


@lru_cache(maxsize=1)
def get_data_database() -> Database:
    """获取 speclabos_data 数据库实例。

    Returns:
        speclabos_data MongoDB 数据库实例。
    """
    settings = get_settings()
    return get_mongo_client()[settings.mongo.data_database]


__all__ = ["get_data_database"]
