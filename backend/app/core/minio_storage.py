"""MinIO 对象存储访问入口。"""

from functools import lru_cache
from minio import Minio

from app.core.config import get_settings


@lru_cache(maxsize=1)
def get_minio_client() -> Minio:
    """创建并缓存 MinIO 客户端。"""
    settings = get_settings()
    return Minio(
        settings.minio.endpoint,
        access_key=settings.minio.access_key,
        secret_key=settings.minio.secret_key,
        secure=settings.minio.secure,
    )


def get_minio_bucket() -> str:
    """获取默认 MinIO bucket 名称。"""
    return get_settings().minio.bucket


__all__ = ["get_minio_bucket", "get_minio_client"]
