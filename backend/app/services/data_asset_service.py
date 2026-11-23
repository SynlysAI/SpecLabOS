"""SmartDataHub 数据资产业务服务。"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException, UploadFile
from minio.error import S3Error

from app.core.config import get_settings
from app.core.minio_storage import get_minio_bucket, get_minio_client
from app.repositories.data_asset_repository import DataAssetRepository


class DataAssetService:
    """处理数据资产上传、归档和查询。"""

    def __init__(
        self,
        repository: DataAssetRepository | None = None,
        minio_client: Any | None = None,
    ) -> None:
        """初始化数据资产服务。

        Args:
            repository: 数据资产仓储，默认使用全局仓储。
            minio_client: MinIO 客户端，默认使用全局客户端。
        """
        self._repository = repository or DataAssetRepository()
        self._minio_client = minio_client or get_minio_client()

    def ingest_file(
        self,
        uploaded_file: UploadFile,
        metadata_text: str,
    ) -> dict[str, Any]:
        """接收单个文件并归档到 MinIO 和 MongoDB。

        Args:
            uploaded_file: 上传的文件对象。
            metadata_text: 采集器传入的元数据 JSON 字符串。

        Returns:
            文件资产落库后的结果。
        """
        metadata = self._parse_metadata(metadata_text)
        collector_id = self._require_text(metadata, "collector_id")
        device_id = self._require_text(metadata, "device_id")
        data_type = self._require_text(metadata, "data_type")
        asset_kind = str(metadata.get("asset_kind") or "file")
        asset_group_id = self._require_text(metadata, "asset_group_id")
        root_name = self._require_text(metadata, "root_name")
        relative_path = self._require_text(metadata, "relative_path")
        filename = str(metadata.get("filename") or uploaded_file.filename or root_name)
        content_type = str(
            metadata.get("content_type") or uploaded_file.content_type or "application/octet-stream"
        )
        file_hash = self._require_text(metadata, "file_hash")
        file_size = self._resolve_file_size(uploaded_file)
        created_at = self._resolve_created_at(metadata)
        storage_bucket = get_minio_bucket()
        storage_key = self._build_storage_key(
            device_id=device_id,
            data_type=data_type,
            created_at=created_at,
            asset_kind=asset_kind,
            root_name=root_name,
            relative_path=relative_path,
        )
        storage_uri = f"minio://{storage_bucket}/{storage_key}"

        self._ensure_bucket(storage_bucket)
        try:
            uploaded_file.file.seek(0)
            self._minio_client.put_object(
                storage_bucket,
                storage_key,
                uploaded_file.file,
                length=file_size,
                content_type=content_type,
            )
        except S3Error as exc:
            raise HTTPException(status_code=502, detail=f"MinIO 上传失败: {exc}") from exc

        record = self._repository.create_file_asset(
            collector_id=collector_id,
            device_id=device_id,
            data_type=data_type,
            asset_kind=asset_kind,
            asset_group_id=asset_group_id,
            root_name=root_name,
            relative_path=relative_path,
            filename=filename,
            content_type=content_type,
            file_size=file_size,
            file_hash=file_hash,
            storage_bucket=storage_bucket,
            storage_key=storage_key,
            storage_uri=storage_uri,
            metadata=metadata,
        )
        return record

    def list_assets(
        self,
        *,
        limit: int = 50,
        keyword: str | None = None,
        device_id: str | None = None,
        collector_id: str | None = None,
        data_type: str | None = None,
        asset_kind: str | None = None,
        ingested_start: datetime | None = None,
        ingested_end: datetime | None = None,
    ) -> tuple[list[dict[str, Any]], int]:
        """查询数据资产列表。

        Args:
            limit: 最大返回数量。
            keyword: 关键词，匹配资产名、文件名或资产组。
            device_id: 设备 ID。
            collector_id: 采集器 ID。
            data_type: 数据类型。
            asset_kind: 资产类型，文件或目录。
            ingested_start: 入库时间下界（含）。
            ingested_end: 入库时间上界（含）。

        Returns:
            资产记录列表和匹配总数。
        """
        return self._repository.list_assets(
            limit=limit,
            keyword=keyword,
            device_id=device_id,
            collector_id=collector_id,
            data_type=data_type,
            asset_kind=asset_kind,
            ingested_start=ingested_start,
            ingested_end=ingested_end,
        )

    def get_overview(self) -> dict[str, Any]:
        """获取 SmartDataHub 数据资产概览。

        Returns:
            数据资产全量统计和分布数据。
        """
        return self._repository.get_overview()

    def get_device_stats(self) -> dict[str, Any]:
        """获取 SmartDataHub 按设备聚合的数据统计。"""
        return self._repository.get_device_stats()


    def list_files_by_type(
        self,
        data_type: str,
        *,
        keyword: str | None = None,
        device_id: str | None = None,
        start_at: str | None = None,
        end_at: str | None = None,
        limit: int = 100,
    ) -> tuple[list[dict[str, Any]], int]:
        """按数据类型查询文件。

        Args:
            data_type: 数据类型。
            keyword: 文件名或路径关键字。
            device_id: 设备 ID。
            start_at: 入库时间下限。
            end_at: 入库时间上限。
            limit: 最大返回数量。

        Returns:
            文件记录列表和匹配总数。
        """
        return self._repository.list_files_by_type(
            data_type,
            keyword=keyword,
            device_id=device_id,
            start_at=start_at,
            end_at=end_at,
            limit=limit,
        )

    def read_text_file(self, file_id: str, *, max_bytes: int = 200_000) -> dict[str, Any]:
        """读取文本文件尾部内容。

        Args:
            file_id: 数据文件 ID。
            max_bytes: 最多读取的尾部字节数。

        Returns:
            文件元信息和可展示的文本内容。
        """
        record = self._repository.get_file(file_id)
        if record is None:
            raise HTTPException(status_code=404, detail="日志文件不存在")

        content_type = str(record.get("content_type") or "")
        filename = str(record.get("filename") or "")
        if not self._is_text_file(content_type, filename):
            raise HTTPException(status_code=415, detail="该文件不是可直接查看的文本日志")

        bucket_name = str(record.get("storage_bucket") or get_minio_bucket())
        storage_key = str(record.get("storage_key") or "")
        response = None
        try:
            response = self._minio_client.get_object(bucket_name, storage_key)
            payload = response.read()
        except S3Error as exc:
            raise HTTPException(status_code=502, detail=f"读取日志文件失败: {exc}") from exc
        finally:
            if response is not None:
                response.close()
                response.release_conn()

        truncated = len(payload) > max_bytes
        text = payload[-max_bytes:].decode("utf-8", errors="replace") if truncated else payload.decode(
            "utf-8",
            errors="replace",
        )
        if truncated:
            text = text.split("\n", 1)[-1]
        return {
            "file_id": file_id,
            "filename": filename,
            "device_id": record.get("device_id", ""),
            "content_type": content_type,
            "file_size": int(record.get("file_size") or len(payload)),
            "truncated": truncated,
            "content": text,
        }

    @staticmethod
    def _is_text_file(content_type: str, filename: str) -> bool:
        """判断文件是否适合按文本日志展示。

        Args:
            content_type: 文件 MIME 类型。
            filename: 文件名。

        Returns:
            文本文件返回 True。
        """
        normalized_type = content_type.lower()
        if normalized_type.startswith("text/") or "json" in normalized_type or "xml" in normalized_type:
            return True
        return filename.lower().endswith((".log", ".txt", ".csv", ".json", ".xml"))

    def list_files_in_window(
        self,
        device_id: str,
        start_at: datetime,
        end_at: datetime,
        limit: int = 200,
    ) -> list[dict[str, Any]]:
        """查询设备在入库时间窗内的数据文件。

        Args:
            device_id: 采集设备 ID。
            start_at: 入库时间下界（含）。
            end_at: 入库时间上界（含）。
            limit: 最大返回数量。

        Returns:
            文件记录列表。
        """
        return self._repository.find_files_in_window(
            device_id,
            start_at.astimezone(timezone.utc).isoformat(),
            end_at.astimezone(timezone.utc).isoformat(),
            limit,
        )

    def list_files(self, asset_id: str, limit: int = 200) -> list[dict[str, Any]]:
        """查询指定资产的文件明细。

        Args:
            asset_id: 资产 ID。
            limit: 最大返回数量。

        Returns:
            文件记录列表。
        """
        return self._repository.list_files(asset_id=asset_id, limit=limit)

    @staticmethod
    def _parse_metadata(metadata_text: str) -> dict[str, Any]:
        """解析上传元数据。

        Args:
            metadata_text: JSON 字符串。

        Returns:
            解析后的元数据字典。
        """
        try:
            metadata = json.loads(metadata_text or "{}")
        except json.JSONDecodeError as exc:
            raise HTTPException(status_code=400, detail="metadata 不是合法 JSON") from exc
        if not isinstance(metadata, dict):
            raise HTTPException(status_code=400, detail="metadata 必须是对象")
        return metadata

    @staticmethod
    def _require_text(metadata: dict[str, Any], key: str) -> str:
        """读取必填文本字段。

        Args:
            metadata: 元数据字典。
            key: 字段名。

        Returns:
            字段文本值。
        """
        value = metadata.get(key)
        if value is None or str(value).strip() == "":
            raise HTTPException(status_code=400, detail=f"metadata.{key} 不能为空")
        return str(value).strip()

    @staticmethod
    def _resolve_file_size(uploaded_file: UploadFile) -> int:
        """获取上传文件大小。

        Args:
            uploaded_file: 上传文件对象。

        Returns:
            文件大小字节数。
        """
        if uploaded_file.size is not None:
            return int(uploaded_file.size)
        current_position = uploaded_file.file.tell()
        uploaded_file.file.seek(0, 2)
        file_size = int(uploaded_file.file.tell())
        uploaded_file.file.seek(current_position)
        return file_size

    @staticmethod
    def _resolve_created_at(metadata: dict[str, Any]) -> datetime:
        """解析创建时间。

        Args:
            metadata: 元数据字典。

        Returns:
            时间对象，解析失败则返回当前 UTC 时间。
        """
        raw_value = metadata.get("created_at")
        if not raw_value:
            return datetime.now(timezone.utc)
        try:
            return datetime.fromisoformat(str(raw_value).replace("Z", "+00:00"))
        except ValueError:
            return datetime.now(timezone.utc)

    @staticmethod
    def _build_storage_key(
        *,
        device_id: str,
        data_type: str,
        created_at: datetime,
        asset_kind: str,
        root_name: str,
        relative_path: str,
    ) -> str:
        """构造 MinIO 对象 key。

        Args:
            device_id: 设备 ID。
            data_type: 数据类型。
            created_at: 创建时间。
            asset_kind: 资产类型。
            root_name: 根目录名称。
            relative_path: 相对路径。

        Returns:
            对象存储 key。
        """
        date_part = created_at.astimezone(timezone.utc).strftime("%Y/%m/%d")
        normalized_path = relative_path.replace("\\", "/").lstrip("/")
        if asset_kind == "file":
            return f"data-assets/{device_id}/{data_type}/{date_part}/{normalized_path}"
        return (
            f"data-assets/{device_id}/{data_type}/{date_part}/"
            f"{root_name}/{normalized_path}"
        )

    def _ensure_bucket(self, bucket_name: str) -> None:
        """确保 MinIO bucket 存在。

        Args:
            bucket_name: bucket 名称。
        """
        try:
            if not self._minio_client.bucket_exists(bucket_name):
                self._minio_client.make_bucket(bucket_name)
        except S3Error as exc:
            raise HTTPException(status_code=502, detail=f"MinIO bucket 初始化失败: {exc}") from exc
