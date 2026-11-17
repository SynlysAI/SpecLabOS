"""SmartAccess 执行端设备图片仓储。"""

from datetime import datetime, timezone


def _now_text() -> str:
    """返回当前 UTC ISO 时间文本。

    Returns:
        当前时间文本。
    """
    return datetime.now(timezone.utc).isoformat()


class SmartAccessImageRepository:
    """SmartAccess 设备图片 MongoDB 仓储。"""

    def __init__(self, database) -> None:
        """初始化仓储。

        Args:
            database: MongoDB 数据库实例。
        """
        self._images = database["smartaccess_device_images"]

    def upsert_image(
        self,
        source_device_id: str,
        storage_name: str,
        content_type: str,
        sha256: str,
    ) -> dict:
        """保存或更新执行端设备图片记录。

        Args:
            source_device_id: 发布图片的执行端 ID。
            storage_name: 图片文件存储名。
            content_type: 图片 MIME 类型。
            sha256: 图片内容哈希。

        Returns:
            图片记录。
        """
        now = _now_text()
        record = {
            "source_device_id": source_device_id,
            "storage_name": storage_name,
            "content_type": content_type,
            "sha256": sha256,
            "updated_at": now,
        }
        self._images.update_one(
            {"source_device_id": source_device_id},
            {"$set": record},
            upsert=True,
        )
        return dict(record)

    def get_image(self, source_device_id: str) -> dict | None:
        """读取指定执行端的设备图片记录。

        Args:
            source_device_id: 执行端 ID。

        Returns:
            图片记录，不存在时返回 None。
        """
        return self._images.find_one({"source_device_id": source_device_id})

    def list_images(self) -> list[dict]:
        """列出全部执行端设备图片记录。

        Returns:
            图片记录列表。
        """
        return list(self._images.find({}))
