"""为历史 SmartDataHub 资产补齐数据目录元数据。

默认仅预检统计；传入 --apply 后写入 data_assets 和 data_asset_files。
"""

from __future__ import annotations

import argparse
from typing import Any

from app.repositories.data_asset_repository import DataAssetRepository


def _relation_updates(record: dict[str, Any]) -> dict[str, Any]:
    """从 metadata 中提取真实业务关系字段。"""
    metadata = record.get("metadata") if isinstance(record.get("metadata"), dict) else {}
    updates: dict[str, Any] = {}
    for field in DataAssetRepository._relation_field_names():
        value = record.get(field) or metadata.get(field)
        if value not in (None, "", []):
            updates[field] = value
    return updates


def _catalog_updates(record: dict[str, Any]) -> dict[str, Any]:
    """生成单条历史记录的目录字段更新。"""
    inferred = DataAssetRepository._infer_dataset_fields(record.get("data_type", ""))
    updates = {
        "dataset_id": record.get("dataset_id") or inferred["dataset_id"],
        "category_id": record.get("category_id") or inferred["category_id"],
    }
    updates.update(_relation_updates(record))
    return updates


def migrate(*, apply: bool = False, repository: DataAssetRepository | None = None) -> dict[str, int]:
    """执行历史资产目录字段迁移。

    Args:
        apply: 是否写入 MongoDB；False 时仅统计待处理记录。
        repository: 可注入的仓储对象，测试使用；缺省连接生产配置。

    Returns:
        资产、文件与关联记录的处理数量。
    """
    repository = repository or DataAssetRepository()
    asset_updates = 0
    file_updates = 0
    asset_file_links = repository.count_asset_file_links()

    for asset in repository._assets.find({}):
        updates = _catalog_updates(asset)
        if apply:
            repository._assets.update_one({"_id": asset["_id"]}, {"$set": updates})
        asset_updates += 1

    for file_record in repository._files.find({}):
        updates = _catalog_updates(file_record)
        if apply:
            repository._files.update_one({"_id": file_record["_id"]}, {"$set": updates})
        file_updates += 1

    return {
        "asset_updates": asset_updates,
        "file_updates": file_updates,
        "asset_file_links": asset_file_links,
        "applied": int(apply),
    }


def main() -> None:
    """命令行入口。"""
    parser = argparse.ArgumentParser(description="迁移 SmartDataHub 历史资产目录字段")
    parser.add_argument("--apply", action="store_true", help="实际写入 MongoDB；默认只预检")
    args = parser.parse_args()
    result = migrate(apply=args.apply)
    mode = "APPLY" if args.apply else "DRY-RUN"
    print(f"[{mode}] assets={result['asset_updates']} files={result['file_updates']} asset_file_links={result['asset_file_links']}")


if __name__ == "__main__":
    main()
