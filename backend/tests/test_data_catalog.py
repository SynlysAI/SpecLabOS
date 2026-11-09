"""SmartDataHub 数据资产设备统计接口测试。"""

from fastapi.testclient import TestClient
from scripts.migrate_data_catalog import migrate

from app.repositories.data_asset_repository import DataAssetRepository
from main import app


def _create_asset(repository: DataAssetRepository, **metadata_overrides):
    """创建一条测试数据资产。"""
    metadata = {
        "collector_id": "collector-a",
        "device_id": "raman_2278",
        "data_type": "raman_raw",
        "asset_kind": "file",
        "asset_group_id": "group-001",
        "root_name": "sample-a.txt",
        "relative_path": "sample-a.txt",
        "filename": "sample-a.txt",
        "file_hash": "hash-a",
    }
    metadata.update(metadata_overrides)
    return repository.create_file_asset(
        collector_id=metadata["collector_id"],
        device_id=metadata["device_id"],
        data_type=metadata["data_type"],
        asset_kind=metadata["asset_kind"],
        asset_group_id=metadata["asset_group_id"],
        root_name=metadata["root_name"],
        relative_path=metadata["relative_path"],
        filename=metadata["filename"],
        content_type="text/plain",
        file_size=int(metadata.get("file_size", 128)),
        file_hash=metadata["file_hash"],
        storage_bucket="speclabos-data",
        storage_key=(
            f"data-assets/{metadata['device_id']}/"
            f"{metadata['data_type']}/{metadata['relative_path']}"
        ),
        storage_uri="minio://speclabos-data/sample-a.txt",
        metadata=metadata,
    )


def test_device_stats_empty_data(fake_database):
    """空库返回稳定的整体统计和空设备列表。"""
    repository = DataAssetRepository(fake_database)

    result = repository.get_device_stats()

    assert result["overall"]["asset_count"] == 0
    assert result["overall"]["file_count"] == 0
    assert result["overall"]["device_count"] == 0
    assert result["items"] == []


def test_device_stats_aggregates_single_device_files_collectors_and_types(fake_database):
    """同一设备下按资产汇总文件大小,并对 Collector 和数据类型去重。"""
    repository = DataAssetRepository(fake_database)
    _create_asset(repository)
    _create_asset(
        repository,
        collector_id="collector-b",
        asset_group_id="group-001",
        root_name="sample-b.txt",
        relative_path="sample-b.txt",
        filename="sample-b.txt",
        file_hash="hash-b",
        file_size=256,
    )
    _create_asset(
        repository,
        data_type="raman_preview",
        asset_group_id="group-002",
        root_name="preview.png",
        relative_path="preview.png",
        filename="preview.png",
        file_hash="hash-c",
        file_size=512,
    )

    result = repository.get_device_stats()
    device = result["items"][0]

    assert device["device_id"] == "raman_2278"
    assert device["asset_count"] == 2
    assert device["file_count"] == 3
    assert device["total_size"] == 896
    assert device["collector_count"] == 2
    assert device["data_type_count"] == 2
    assert result["overall"]["asset_count"] == 2
    assert result["overall"]["file_count"] == 3


def test_device_stats_sorts_multiple_devices_by_asset_count(fake_database):
    """多设备统计按资产数和文件数降序展示。"""
    repository = DataAssetRepository(fake_database)
    _create_asset(repository, device_id="nmr_1000", data_type="nmr_raw")
    _create_asset(
        repository,
        device_id="raman_2278",
        asset_group_id="group-002",
        file_hash="hash-b",
    )
    _create_asset(
        repository,
        device_id="raman_2278",
        asset_group_id="group-003",
        file_hash="hash-c",
    )

    result = repository.get_device_stats()

    assert [item["device_id"] for item in result["items"]] == ["raman_2278", "nmr_1000"]
    assert result["overall"]["device_count"] == 2


def test_data_routes_return_device_stats_and_remove_catalog_routes(fake_database, monkeypatch):
    """数据中心只暴露 SmartDataHub 设备统计和资产接口。"""
    repository = DataAssetRepository(fake_database)
    _create_asset(repository)
    monkeypatch.setattr("app.services.data_asset_service.DataAssetRepository", lambda: repository)
    client = TestClient(app)

    stats_response = client.get("/api/data/device-stats")
    assets_response = client.get("/api/data/assets", params={"device_id": "raman_2278"})

    assert stats_response.status_code == 200
    assert stats_response.json()["items"][0]["device_id"] == "raman_2278"
    assert assets_response.status_code == 200
    assert assets_response.json()["total"] == 1

    removed_paths = [
        "/api/data/catalog/overview",
        "/api/data/catalog/datasets",
        "/api/data/catalog/collections",
        "/api/data/catalog/relationships",
    ]
    for path in removed_paths:
        assert client.get(path).status_code == 404

    assert client.post("/api/data/catalog/import-jobs").status_code == 404


def test_data_catalog_migration_dry_run_and_apply(fake_database):
    """历史目录迁移默认不改数据，显式 apply 后补齐字段。"""
    repository = DataAssetRepository(fake_database)
    _create_asset(repository)
    _create_asset(
        repository,
        asset_group_id="group-002",
        root_name="sample-b.txt",
        relative_path="sample-b.txt",
        filename="sample-b.txt",
        file_hash="hash-b",
    )
    legacy_fields = [
        "dataset_id",
        "category_id",
        "experiment_id",
        "workflow_run_id",
        "task_id",
        "device_run_id",
        "sample_id",
        "operator",
        "tags",
    ]
    unset = {field: "" for field in legacy_fields}
    repository._assets.update_many({}, {"$unset": unset})
    repository._files.update_many({}, {"$unset": unset})

    dry_run = migrate(repository=repository)
    assert dry_run["asset_updates"] == 2
    assert dry_run["file_updates"] == 2
    assert dry_run["asset_file_links"] == 2
    assert dry_run["applied"] == 0
    assert repository._assets.find_one({}, {"_id": 0}).get("dataset_id") is None

    applied = migrate(repository=repository, apply=True)
    assert applied["applied"] == 1
    asset = repository._assets.find_one({}, {"_id": 0})
    file_record = repository._files.find_one({}, {"_id": 0})
    assert asset["dataset_id"] == "raman_spectrum"
    assert asset["category_id"] == "spectrum"
    assert file_record["dataset_id"] == "raman_spectrum"
