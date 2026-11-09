"""SmartDataHub 数据资产仓储。"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid5

from app.core.data_db import get_data_database


UUID_NAMESPACE = UUID("b2c3cc4b-9f1d-4f4a-9c1f-0d4f0f02dfad")


class DataAssetRepository:
    """管理 SmartDataHub 数据资产主记录与文件明细。"""

    ASSET_COLLECTION = "data_assets"
    FILE_COLLECTION = "data_asset_files"

    def __init__(self, database=None) -> None:
        """初始化仓储并创建索引。"""
        database = database or get_data_database()
        self._assets = database[self.ASSET_COLLECTION]
        self._files = database[self.FILE_COLLECTION]
        self._assets.create_index([("asset_key", 1)], unique=True, sparse=True)
        self._assets.create_index([("asset_group_id", 1), ("created_at", -1)])
        self._assets.create_index([("device_id", 1), ("created_at", -1)])
        self._assets.create_index([("data_type", 1), ("created_at", -1)])
        self._assets.create_index([("dataset_id", 1), ("ingested_at", -1)])
        self._assets.create_index([("category_id", 1), ("ingested_at", -1)])
        self._assets.create_index([("workflow_run_id", 1)], sparse=True)
        self._assets.create_index([("task_id", 1)], sparse=True)
        self._assets.create_index([("experiment_id", 1)], sparse=True)
        self._assets.create_index([("sample_id", 1)], sparse=True)
        self._files.create_index([("file_key", 1)], unique=True, sparse=True)
        self._files.create_index([("asset_id", 1), ("relative_path", 1)], unique=True)
        self._files.create_index([("asset_group_id", 1), ("relative_path", 1)])
        self._files.create_index([("device_id", 1), ("created_at", -1)])
        self._files.create_index([("dataset_id", 1), ("ingested_at", -1)])

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
        """创建或更新单个文件资产。"""
        now = _now_text()
        asset_key = self._build_asset_key(device_id, data_type, asset_group_id)
        asset_id = self._resolve_asset_id(asset_key)
        file_key = self._build_file_key(asset_key, relative_path)
        file_id = self._resolve_file_id(file_key)
        catalog_fields = self._resolve_catalog_fields(metadata, data_type)

        file_doc = {
            "file_id": file_id,
            "file_key": file_key,
            "asset_id": asset_id,
            "collector_id": collector_id,
            "device_id": device_id,
            "dataset_id": catalog_fields["dataset_id"],
            "category_id": catalog_fields["category_id"],
            "data_type": data_type,
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
            **catalog_fields["relation_fields"],
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
            "dataset_id": catalog_fields["dataset_id"],
            "category_id": catalog_fields["category_id"],
            "root_name": root_name,
            "filename": filename,
            "file_count": int(self._files.count_documents({"asset_id": asset_id})),
            "total_size": int(
                sum(item.get("file_size", 0) for item in self._files.find({"asset_id": asset_id}))
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
            **catalog_fields["relation_fields"],
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
        device_id: str | None = None,
    ) -> tuple[list[dict], int]:
        """查询 SmartDataHub 数据资产列表。"""
        query = {"device_id": device_id} if device_id else {}
        total = int(self._assets.count_documents(query))
        items = list(self._assets.find(query).sort("ingested_at", -1).limit(limit))
        return [self._normalize_asset(item) for item in items], total

    def get_overview(self) -> dict[str, Any]:
        """获取 SmartDataHub 数据资产全量概览。"""
        summary = self._resolve_overview_summary()
        summary["device_count"] = self._count_distinct_text("device_id")
        summary["collector_count"] = self._count_distinct_text("collector_id")
        summary["data_type_distribution"] = self._group_distribution("data_type")
        summary["device_distribution"] = self._group_distribution("device_id")
        summary["collector_distribution"] = self._group_distribution("collector_id")
        return summary

    def get_device_stats(self) -> dict[str, Any]:
        """按设备聚合 SmartDataHub 数据资产统计。"""
        grouped: dict[str, dict[str, Any]] = {}
        for asset in self._assets.find({"device_id": {"$nin": [None, ""]}}):
            device_id = str(asset.get("device_id") or "")
            if not device_id:
                continue
            row = grouped.setdefault(
                device_id,
                {
                    "device_id": device_id,
                    "asset_count": 0,
                    "file_count": 0,
                    "total_size": 0,
                    "collector_ids": set(),
                    "data_types": set(),
                    "latest_ingested_at": "",
                },
            )
            row["asset_count"] += 1
            row["file_count"] += int(asset.get("file_count") or 0)
            row["total_size"] += int(asset.get("total_size") or 0)
            if asset.get("collector_id"):
                row["collector_ids"].add(str(asset["collector_id"]))
            if asset.get("data_type"):
                row["data_types"].add(str(asset["data_type"]))
            latest = str(asset.get("ingested_at") or "")
            if latest > row["latest_ingested_at"]:
                row["latest_ingested_at"] = latest

        items = [
            {
                "device_id": row["device_id"],
                "asset_count": row["asset_count"],
                "file_count": row["file_count"],
                "total_size": row["total_size"],
                "collector_count": len(row["collector_ids"]),
                "data_type_count": len(row["data_types"]),
                "latest_ingested_at": row["latest_ingested_at"],
            }
            for row in grouped.values()
        ]
        items.sort(
            key=lambda item: (
                -item["asset_count"],
                -item["file_count"],
                item["device_id"],
            )
        )
        return {"overall": self.get_overview(), "items": items}

    def count_asset_file_links(self) -> int:
        """统计当前资产与文件记录的关联规模。"""
        return int(self._files.count_documents({}))

    def list_files(self, asset_id: str, limit: int = 200) -> list[dict]:
        """查询指定资产的文件明细。"""
        return list(
            self._files.find({"asset_id": asset_id}).sort("relative_path", 1).limit(limit)
        )

    def _normalize_asset(self, item: dict[str, Any]) -> dict[str, Any]:
        """补齐旧资产缺失的目录和关系字段。"""
        normalized = dict(item)
        if not normalized.get("dataset_id") or not normalized.get("category_id"):
            normalized.update(self._infer_dataset_fields(normalized.get("data_type", "")))
        metadata = normalized.get("metadata") if isinstance(normalized.get("metadata"), dict) else {}
        for field in self._relation_field_names():
            if not normalized.get(field) and metadata.get(field):
                normalized[field] = metadata.get(field)
        return normalized

    def _resolve_catalog_fields(self, metadata: dict[str, Any], data_type: str) -> dict[str, Any]:
        """从上传元数据解析兼容性目录字段。"""
        inferred = self._infer_dataset_fields(data_type)
        dataset_id = str(metadata.get("dataset_id") or inferred["dataset_id"]).strip()
        category_id = str(metadata.get("category_id") or inferred["category_id"]).strip()
        relation_fields: dict[str, Any] = {}
        for field in self._relation_field_names():
            value = metadata.get(field)
            if value is not None and str(value).strip() != "":
                relation_fields[field] = value if field == "tags" and isinstance(value, list) else str(value).strip()
        relation_fields.setdefault("tags", metadata.get("tags") if isinstance(metadata.get("tags"), list) else [])
        return {"dataset_id": dataset_id, "category_id": category_id, "relation_fields": relation_fields}

    @classmethod
    def _relation_field_names(cls) -> list[str]:
        """资产支持的业务关系字段。"""
        return [
            "experiment_id",
            "workflow_run_id",
            "task_id",
            "device_run_id",
            "sample_id",
            "operator",
            "tags",
        ]

    @classmethod
    def _infer_dataset_fields(cls, data_type: str) -> dict[str, str]:
        """根据 data_type 为旧资产推断兼容性目录字段。"""
        normalized = str(data_type or "").lower()
        if "raman" in normalized:
            return {"dataset_id": "raman_spectrum", "category_id": "spectrum"}
        if "nmr" in normalized:
            return {"dataset_id": "nmr_raw_spectrum", "category_id": "spectrum"}
        if "gpc" in normalized or "lcms" in normalized or "chrom" in normalized:
            return {"dataset_id": "chromatography_result", "category_id": "chromatography"}
        if "workflow" in normalized:
            return {"dataset_id": "workflow_artifact", "category_id": "workflow_artifact"}
        if "log" in normalized:
            return {"dataset_id": "device_log", "category_id": "device_log"}
        if "compute" in normalized or "result" in normalized or "analysis" in normalized:
            return {"dataset_id": "device_run_result", "category_id": "computed_result"}
        return {"dataset_id": "device_run_result", "category_id": "raw_experiment"}

    def _resolve_overview_summary(self) -> dict[str, Any]:
        """聚合资产全量汇总指标。"""
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
        """统计指定字段的非空去重数量。"""
        values = self._assets.distinct(field_name)
        return len([value for value in values if value])

    def _group_distribution(self, field_name: str, limit: int = 10) -> list[dict[str, Any]]:
        """按指定字段聚合资产分布。"""
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
        """规范化聚合分布项。"""
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
        """根据资产业务键生成稳定的资产 ID。"""
        return str(uuid5(UUID_NAMESPACE, asset_key))

    @staticmethod
    def _resolve_file_id(file_key: str) -> str:
        """根据文件业务键生成稳定的文件 ID。"""
        return str(uuid5(UUID_NAMESPACE, file_key))

    @staticmethod
    def _build_asset_key(device_id: str, data_type: str, asset_group_id: str) -> str:
        """构造资产业务唯一键。"""
        return f"{device_id}:{data_type}:{asset_group_id}"

    @staticmethod
    def _build_file_key(asset_key: str, relative_path: str) -> str:
        """构造文件业务唯一键。"""
        normalized_path = relative_path.replace("\\", "/").lstrip("/")
        return f"{asset_key}:{normalized_path}"


def _now_text() -> str:
    """获取当前 UTC 时间文本。"""
    return datetime.now(timezone.utc).isoformat()
