"""SmartDataHub 数据资产仓储。"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid5

from app.core.data_db import get_data_database


UUID_NAMESPACE = UUID("b2c3cc4b-9f1d-4f4a-9c1f-0d4f0f02dfad")


class DataAssetRepository:
    """管理数据资产主记录与文件明细。"""

    ASSET_COLLECTION = "data_assets"
    FILE_COLLECTION = "data_asset_files"

    def __init__(self) -> None:
        """初始化仓储并创建索引。"""
        database = get_data_database()
        self._assets = database[self.ASSET_COLLECTION]
        self._files = database[self.FILE_COLLECTION]
        self._assets.create_index([("asset_key", 1)], unique=True, sparse=True)
        self._assets.create_index([("asset_group_id", 1), ("created_at", -1)])
        self._assets.create_index([("device_id", 1), ("created_at", -1)])
        self._assets.create_index([("data_type", 1), ("created_at", -1)])
        self._files.create_index([("file_key", 1)], unique=True, sparse=True)
        self._files.create_index([("asset_id", 1), ("relative_path", 1)], unique=True)
        self._files.create_index([("asset_group_id", 1), ("relative_path", 1)])
        self._files.create_index([("device_id", 1), ("created_at", -1)])

    def create_file_asset(
        self,
        *,
        collector_id: str,
        device_id: str,
        data_type: str,
        asset_kind: str,
        asset_group_id: str,
        root_name: str,
        relative_path: str,
        filename: str,
        content_type: str,
        file_size: int,
        file_hash: str,
        storage_bucket: str,
        storage_key: str,
        storage_uri: str,
        metadata: dict[str, Any],
    ) -> dict:
        """创建或更新单个文件资产。

        Args:
            collector_id: 采集器 ID。
            device_id: 设备 ID。
            data_type: 数据类型。
            asset_kind: 资产类型。
            asset_group_id: 资产组 ID。
            root_name: 根目录名称。
            relative_path: 相对路径。
            filename: 文件名。
            content_type: MIME 类型。
            file_size: 文件大小。
            file_hash: 文件哈希。
            storage_bucket: MinIO bucket。
            storage_key: MinIO object key。
            storage_uri: MinIO URI。
            metadata: 附加元数据。

        Returns:
            文件资产记录。
        """
        now = _now_text()
        asset_key = self._build_asset_key(device_id, data_type, asset_group_id)
        asset_id = self._resolve_asset_id(asset_key)
        file_key = self._build_file_key(asset_key, relative_path)
        file_id = self._resolve_file_id(file_key)

        file_doc = {
            "file_id": file_id,
            "file_key": file_key,
            "asset_id": asset_id,
            "collector_id": collector_id,
            "device_id": device_id,
            "asset_group_id": asset_group_id,
            "root_name": root_name,
            "relative_path": relative_path,
            "filename": filename,
            "content_type": content_type,
            "file_size": file_size,
            "file_hash": file_hash,
            "storage_backend": "minio",
            "storage_bucket": storage_bucket,
            "storage_key": storage_key,
            "storage_uri": storage_uri,
            "upload_status": "completed",
            "created_at": now,
            "ingested_at": now,
            "metadata": metadata,
        }
        self._files.update_one(
            {"file_key": file_key},
            {"$set": file_doc},
            upsert=True,
        )

        asset_doc = {
            "asset_id": asset_id,
            "asset_key": asset_key,
            "asset_kind": asset_kind,
            "asset_group_id": asset_group_id,
            "collector_id": collector_id,
            "device_id": device_id,
            "data_type": data_type,
            "root_name": root_name,
            "filename": filename,
            "file_count": int(self._files.count_documents({"asset_id": asset_id})),
            "total_size": int(
                sum(
                    item.get("file_size", 0)
                    for item in self._files.find({"asset_id": asset_id})
                )
            ),
            "file_hash": file_hash,
            "storage_backend": "minio",
            "storage_bucket": storage_bucket,
            "storage_prefix": storage_key.rsplit("/", 1)[0] + "/",
            "storage_uri": storage_uri,
            "upload_status": "completed",
            "created_at": now,
            "ingested_at": now,
            "metadata": metadata,
        }
        self._assets.update_one(
            {"asset_key": asset_key},
            {"$set": asset_doc},
            upsert=True,
        )
        return file_doc

    def list_assets(
        self,
        *,
        limit: int = 50,
        keyword: str | None = None,
        device_id: str | None = None,
        collector_id: str | None = None,
        data_type: str | None = None,
    ) -> tuple[list[dict], int]:
        """查询数据资产列表。

        Args:
            limit: 最大返回数量。
            keyword: 关键词，匹配资产名、文件名或资产组。
            device_id: 设备 ID。
            collector_id: 采集器 ID。
            data_type: 数据类型。

        Returns:
            资产记录列表和匹配总数。
        """
        query = self._build_asset_query(
            keyword=keyword,
            device_id=device_id,
            collector_id=collector_id,
            data_type=data_type,
        )
        total = int(self._assets.count_documents(query))
        items = list(self._assets.find(query).sort("ingested_at", -1).limit(limit))
        return items, total

    def get_overview(self) -> dict[str, Any]:
        """获取 SmartDataHub 数据资产全量概览。

        Returns:
            包含全量统计和常用分布的概览数据。
        """
        summary = self._resolve_overview_summary()
        summary["device_count"] = self._count_distinct_text("device_id")
        summary["collector_count"] = self._count_distinct_text("collector_id")
        summary["data_type_distribution"] = self._group_distribution("data_type")
        summary["device_distribution"] = self._group_distribution("device_id")
        summary["collector_distribution"] = self._group_distribution("collector_id")
        return summary

    def list_files(self, asset_id: str, limit: int = 200) -> list[dict]:
        """查询指定资产的文件明细。

        Args:
            asset_id: 资产 ID。
            limit: 最大返回数量。

        Returns:
            文件记录列表。
        """
        return list(
            self._files.find({"asset_id": asset_id}).sort("relative_path", 1).limit(limit)
        )

    @staticmethod
    def _build_asset_query(
        *,
        keyword: str | None = None,
        device_id: str | None = None,
        collector_id: str | None = None,
        data_type: str | None = None,
    ) -> dict[str, Any]:
        """构造资产列表查询条件。

        Args:
            keyword: 关键词，匹配资产名、文件名或资产组。
            device_id: 设备 ID。
            collector_id: 采集器 ID。
            data_type: 数据类型。

        Returns:
            MongoDB 查询条件。
        """
        query: dict[str, Any] = {}
        if device_id:
            query["device_id"] = device_id
        if collector_id:
            query["collector_id"] = collector_id
        if data_type:
            query["data_type"] = data_type
        if keyword:
            keyword_filter = {"$regex": keyword, "$options": "i"}
            query["$or"] = [
                {"root_name": keyword_filter},
                {"filename": keyword_filter},
                {"asset_group_id": keyword_filter},
                {"asset_key": keyword_filter},
            ]
        return query

    def _resolve_overview_summary(self) -> dict[str, Any]:
        """聚合资产全量汇总指标。

        Returns:
            资产数量、文件数量、总大小和最近入库时间。
        """
        result = list(
            self._assets.aggregate(
                [
                    {
                        "$group": {
                            "_id": None,
                            "asset_count": {"$sum": 1},
                            "file_count": {"$sum": {"$ifNull": ["$file_count", 0]}},
                            "total_size": {"$sum": {"$ifNull": ["$total_size", 0]}},
                            "latest_ingested_at": {"$max": "$ingested_at"},
                        }
                    }
                ]
            )
        )
        if not result:
            return {
                "asset_count": 0,
                "file_count": 0,
                "total_size": 0,
                "latest_ingested_at": "",
            }
        summary = result[0]
        return {
            "asset_count": int(summary.get("asset_count") or 0),
            "file_count": int(summary.get("file_count") or 0),
            "total_size": int(summary.get("total_size") or 0),
            "latest_ingested_at": str(summary.get("latest_ingested_at") or ""),
        }

    def _count_distinct_text(self, field_name: str) -> int:
        """统计指定字段的非空去重数量。

        Args:
            field_name: 需要统计的字段名。

        Returns:
            非空字段值的去重数量。
        """
        values = self._assets.distinct(field_name)
        return len([value for value in values if value])

    def _group_distribution(self, field_name: str, limit: int = 10) -> list[dict[str, Any]]:
        """按指定字段聚合资产分布。

        Args:
            field_name: 分组字段名。
            limit: 最大返回分组数量。

        Returns:
            分组统计列表。
        """
        rows = self._assets.aggregate(
            [
                {"$match": {field_name: {"$nin": [None, ""]}}},
                {
                    "$group": {
                        "_id": f"${field_name}",
                        "asset_count": {"$sum": 1},
                        "file_count": {"$sum": {"$ifNull": ["$file_count", 0]}},
                        "total_size": {"$sum": {"$ifNull": ["$total_size", 0]}},
                        "latest_ingested_at": {"$max": "$ingested_at"},
                    }
                },
                {"$sort": {"asset_count": -1, "file_count": -1}},
                {"$limit": limit},
            ]
        )
        return [self._normalize_distribution_item(row) for row in rows]

    @staticmethod
    def _normalize_distribution_item(row: dict[str, Any]) -> dict[str, Any]:
        """规范化聚合分布项。

        Args:
            row: MongoDB 聚合结果行。

        Returns:
            前端可直接消费的分布项。
        """
        key = str(row.get("_id") or "")
        return {
            "key": key,
            "label": key,
            "asset_count": int(row.get("asset_count") or 0),
            "file_count": int(row.get("file_count") or 0),
            "total_size": int(row.get("total_size") or 0),
            "latest_ingested_at": str(row.get("latest_ingested_at") or ""),
        }

    @staticmethod
    def _resolve_asset_id(asset_key: str) -> str:
        """根据资产业务键生成稳定的资产 ID。

        Args:
            asset_key: 资产业务唯一键。

        Returns:
            确定性 UUID 格式的资产 ID。
        """
        return str(uuid5(UUID_NAMESPACE, asset_key))

    @staticmethod
    def _resolve_file_id(file_key: str) -> str:
        """根据文件业务键生成稳定的文件 ID。

        Args:
            file_key: 文件业务唯一键。

        Returns:
            确定性 UUID 格式的文件 ID。
        """
        return str(uuid5(UUID_NAMESPACE, file_key))

    @staticmethod
    def _build_asset_key(device_id: str, data_type: str, asset_group_id: str) -> str:
        """构造资产业务唯一键。

        Args:
            device_id: 设备 ID。
            data_type: 数据类型。
            asset_group_id: 资产组 ID。

        Returns:
            资产业务唯一键。
        """
        return f"{device_id}:{data_type}:{asset_group_id}"

    @staticmethod
    def _build_file_key(asset_key: str, relative_path: str) -> str:
        """构造文件业务唯一键。

        Args:
            asset_key: 资产业务唯一键。
            relative_path: 文件相对路径。

        Returns:
            文件业务唯一键。
        """
        normalized_path = relative_path.replace("\\", "/").lstrip("/")
        return f"{asset_key}:{normalized_path}"


def _now_text() -> str:
    """获取当前 UTC 时间文本。"""
    return datetime.now(timezone.utc).isoformat()
