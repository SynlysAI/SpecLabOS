"""日志路由测试。"""

from fastapi.testclient import TestClient

from app.api.routes.logs import get_data_asset_service
from app.repositories.data_asset_repository import DataAssetRepository
from app.services.data_asset_service import DataAssetService
from main import app


def _create_log_file(repository: DataAssetRepository, **overrides):
    """创建一条日志类测试文件。"""
    metadata = {
        "collector_id": "collector-a",
        "device_id": "raman-01",
        "data_type": "device_log",
        "asset_kind": "file",
        "asset_group_id": "raman-log",
        "root_name": "raman.log",
        "relative_path": "raman.log",
        "filename": "raman.log",
        "file_hash": "hash-raman",
        "watcher_name": "raman-watcher",
        "file_size": 128,
    }
    metadata.update(overrides)
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
        file_size=int(metadata["file_size"]),
        file_hash=metadata["file_hash"],
        storage_bucket="speclabos-data",
        storage_key=f"data-assets/{metadata['relative_path']}",
        storage_uri=f"minio://speclabos-data/{metadata['relative_path']}",
        metadata=metadata,
    )


def test_list_logs_returns_device_log_files(fake_database):
    """日志列表只返回数据中心的日志类文件。"""
    repository = DataAssetRepository(fake_database)
    _create_log_file(repository)
    _create_log_file(
        repository,
        data_type="result_data",
        asset_group_id="result",
        root_name="result.csv",
        relative_path="result.csv",
        filename="result.csv",
        file_hash="hash-result",
    )
    app.dependency_overrides[get_data_asset_service] = lambda: DataAssetService(
        repository=repository,
        minio_client=object(),
    )
    client = TestClient(app)

    response = client.get("/api/logs", params={"days": 0})
    app.dependency_overrides.pop(get_data_asset_service, None)

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["filename"] == "raman.log"
    assert data["items"][0]["device_id"] == "raman-01"
    assert data["items"][0]["watcher_name"] == "raman-watcher"
