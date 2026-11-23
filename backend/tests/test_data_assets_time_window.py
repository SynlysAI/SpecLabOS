"""数据资产入库时间窗口筛选测试。"""

from datetime import datetime, timezone

import mongomock
from fastapi.testclient import TestClient

from app.repositories.data_asset_repository import DataAssetRepository
from app.services.data_asset_service import DataAssetService
from main import app


def _repository() -> DataAssetRepository:
    """提供基于 mongomock 的资产仓储。"""
    return DataAssetRepository(database=mongomock.MongoClient()["speclabos_test"])


def _seed(repository: DataAssetRepository, asset_id: str, ingested_at: str) -> None:
    """插入一条最小可用的资产文档。"""
    repository._assets.insert_one(
        {
            "asset_id": asset_id,
            "asset_key": f"key-{asset_id}",
            "asset_kind": "file",
            "device_id": "nmr_2278",
            "data_type": "spectrum",
            "root_name": f"{asset_id}.dx",
            "filename": f"{asset_id}.dx",
            "ingested_at": ingested_at,
            "created_at": ingested_at,
        }
    )


def _utc(text: str) -> datetime:
    """把无时区 ISO 文本解析为 UTC 时间。"""
    return datetime.fromisoformat(text).replace(tzinfo=timezone.utc)


def test_list_assets_filters_by_ingested_window():
    """入库时间窗口应只保留范围内的资产。"""
    repository = _repository()
    _seed(repository, "early", "2026-11-23T01:00:00.000000+00:00")
    _seed(repository, "within", "2026-11-23T03:30:00.000000+00:00")
    _seed(repository, "late", "2026-11-23T09:00:00.000000+00:00")
    items, total = repository.list_assets(
        device_id="nmr_2278",
        ingested_start=_utc("2026-11-23T02:00:00"),
        ingested_end=_utc("2026-11-23T08:00:00"),
    )
    assert total == 1
    assert [item["asset_id"] for item in items] == ["within"]


def test_list_assets_supports_open_ended_bounds():
    """仅提供一端边界时应按单边筛选。"""
    repository = _repository()
    _seed(repository, "first", "2026-11-23T01:00:00.000000+00:00")
    _seed(repository, "second", "2026-11-24T01:00:00.000000+00:00")
    only_after, total_after = repository.list_assets(ingested_start=_utc("2026-11-23T12:00:00"))
    assert total_after == 1
    assert only_after[0]["asset_id"] == "second"
    only_before, total_before = repository.list_assets(ingested_end=_utc("2026-11-23T12:00:00"))
    assert total_before == 1
    assert only_before[0]["asset_id"] == "first"


def test_route_rejects_invalid_time_bound():
    """非法时间参数应返回 400。"""
    client = TestClient(app)
    response = client.get("/api/data/assets", params={"ingested_start": "not-a-date"})
    assert response.status_code == 400


def test_route_parses_time_bounds_with_timezone(monkeypatch):
    """路由应把 Z/带偏移时间统一解析为 UTC 传给服务层。"""
    captured: dict = {}

    def fake_list_assets(self, **kwargs):
        captured.update(kwargs)
        return [], 0

    monkeypatch.setattr(DataAssetService, "list_assets", fake_list_assets)
    client = TestClient(app)
    response = client.get(
        "/api/data/assets",
        params={
            "ingested_start": "2026-11-23T02:00:00Z",
            "ingested_end": "2026-11-23T08:00:00+08:00",
        },
    )
    assert response.status_code == 200
    assert captured["ingested_start"] == datetime(2026, 11, 23, 2, 0, tzinfo=timezone.utc)
    assert captured["ingested_end"] == datetime(2026, 11, 23, 0, 0, tzinfo=timezone.utc)
