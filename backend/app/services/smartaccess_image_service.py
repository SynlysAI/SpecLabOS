"""SmartAccess 执行端设备图片业务服务。"""

import hashlib
from pathlib import Path

from fastapi import HTTPException

from app.core.config import get_settings
from app.repositories.smartaccess_image_repository import SmartAccessImageRepository


SUPPORTED_IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png", ".webp", ".gif")
MAX_IMAGE_BYTES = 5 * 1024 * 1024
CONTENT_TYPE_EXTENSIONS = {
    "image/jpeg": ".jpg",
    "image/jpg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/gif": ".gif",
}


class SmartAccessImageService:
    """管理执行端上传的设备图片。"""

    def __init__(self, repository: SmartAccessImageRepository) -> None:
        """初始化服务。

        Args:
            repository: 设备图片仓储。
        """
        self._repository = repository

    def save_image(
        self,
        source_device_id: str,
        filename: str,
        content_type: str,
        content: bytes,
    ) -> dict:
        """保存执行端上传的设备图片。

        Args:
            source_device_id: 上传图片的执行端 ID。
            filename: 原始文件名，用于推断扩展名。
            content_type: 图片 MIME 类型。
            content: 图片二进制内容。

        Returns:
            含图片访问地址的记录。

        Raises:
            HTTPException: 参数不合法或图片目录未配置时抛出。
        """
        device_id = (source_device_id or "").strip()
        if not device_id:
            raise HTTPException(status_code=400, detail="source_device_id 不能为空")
        if not content:
            raise HTTPException(status_code=400, detail="图片内容不能为空")
        if len(content) > MAX_IMAGE_BYTES:
            raise HTTPException(status_code=413, detail="图片大小不能超过 5MB")

        extension = self._resolve_extension(filename, content_type)
        image_dir = self._resolve_image_dir()
        image_dir.mkdir(parents=True, exist_ok=True)

        digest = hashlib.sha256(content).hexdigest()
        device_hash = hashlib.sha1(device_id.encode("utf-8")).hexdigest()[:16]
        storage_name = f"smartaccess-device-{device_hash}{extension}"
        target_path = image_dir / storage_name

        previous = self._repository.get_image(device_id)
        if previous and previous.get("storage_name") != storage_name:
            previous_path = image_dir / str(previous.get("storage_name") or "")
            if previous_path.is_file():
                previous_path.unlink(missing_ok=True)

        target_path.write_bytes(content)
        record = self._repository.upsert_image(
            device_id,
            storage_name,
            content_type or self._extension_content_type(extension),
            digest,
        )
        record["image_url"] = self._build_image_url(storage_name, digest)
        return record

    def get_image_url(self, source_device_id: str) -> str:
        """读取执行端设备图片访问地址。

        Args:
            source_device_id: 执行端 ID。

        Returns:
            图片访问地址；未上传时返回空字符串。
        """
        record = self._repository.get_image(source_device_id)
        if not record:
            return ""
        return self._build_image_url(
            str(record.get("storage_name") or ""),
            str(record.get("sha256") or ""),
        )

    def list_image_urls(self) -> dict[str, str]:
        """列出全部执行端设备图片访问地址。

        Returns:
            执行端 ID 到图片访问地址的映射。
        """
        urls: dict[str, str] = {}
        for record in self._repository.list_images():
            device_id = str(record.get("source_device_id") or "")
            if not device_id:
                continue
            urls[device_id] = self._build_image_url(
                str(record.get("storage_name") or ""),
                str(record.get("sha256") or ""),
            )
        return urls

    @staticmethod
    def _resolve_extension(filename: str, content_type: str) -> str:
        """根据文件名或 MIME 类型解析图片扩展名。

        Args:
            filename: 原始文件名。
            content_type: 图片 MIME 类型。

        Returns:
            小写扩展名。

        Raises:
            HTTPException: 不支持的图片格式时抛出。
        """
        suffix = Path(filename or "").suffix.lower()
        if suffix in SUPPORTED_IMAGE_EXTENSIONS:
            return suffix
        mapped = CONTENT_TYPE_EXTENSIONS.get((content_type or "").lower())
        if mapped:
            return mapped
        raise HTTPException(status_code=400, detail="仅支持 jpg/png/webp/gif 图片")

    @staticmethod
    def _extension_content_type(extension: str) -> str:
        """根据扩展名返回图片 MIME 类型。

        Args:
            extension: 图片扩展名。

        Returns:
            图片 MIME 类型。
        """
        for content_type, mapped in CONTENT_TYPE_EXTENSIONS.items():
            if mapped == extension:
                return content_type
        return "application/octet-stream"

    @staticmethod
    def _resolve_image_dir() -> Path:
        """解析设备图片存储目录。

        Returns:
            图片目录路径。

        Raises:
            HTTPException: 未配置图片目录时抛出。
        """
        image_dir = (get_settings().device_images.image_dir or "").strip()
        if not image_dir:
            raise HTTPException(
                status_code=500,
                detail="未配置 device_images.image_dir，无法保存设备图片",
            )
        return Path(image_dir)

    @staticmethod
    def _build_image_url(storage_name: str, digest: str) -> str:
        """构造设备图片访问地址。

        Args:
            storage_name: 图片文件存储名。
            digest: 图片内容哈希，用于缓存失效。

        Returns:
            图片访问地址；存储名为空时返回空字符串。
        """
        if not storage_name:
            return ""
        stem = Path(storage_name).stem
        version = (digest or "")[:8]
        return f"/api/device-images/{stem}?v={version}"
