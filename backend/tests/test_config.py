"""配置加载测试。"""

from pathlib import Path

import pytest

import main
from app.core.config import Settings, get_default_config_path, load_settings


def test_load_settings_reads_yaml(tmp_path: Path) -> None:
    """验证配置加载函数可以读取 YAML 文件。"""
    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        """
app:
  name: SpecLabOS
  host: 127.0.0.1
  port: 8000
mongo:
  uri: mongodb://localhost:27017
  database: spec_labos
runtime:
  sim_mode: true
  status_poll_interval_seconds: 10
  runner_interval_seconds: 1
devices:
  enabled_keys: [nmr_2278]
""".strip(),
        encoding="utf-8",
    )

    settings = load_settings(config_file)

    assert isinstance(settings, Settings)
    assert settings.mongo.database == "spec_labos"
    assert settings.runtime.sim_mode is True
    assert settings.devices.enabled_keys == ["nmr_2278"]


def test_get_default_config_path_from_backend_file() -> None:
    """验证默认配置文件路径可以从 backend 子路径明确解析。"""
    backend_file = Path("E:/xx_project/SpecLabOS/backend/app/core/config.py")

    config_path = get_default_config_path(backend_file)

    assert config_path == Path("E:/xx_project/SpecLabOS/config.yaml")


def test_create_app_uses_settings_title(monkeypatch: pytest.MonkeyPatch) -> None:
    """验证应用标题来自配置对象。"""
    settings = Settings.model_validate(
        {
            "app": {
                "name": "SpecLabOS Test",
                "host": "127.0.0.1",
                "port": 8000,
            },
            "mongo": {
                "uri": "mongodb://localhost:27017",
                "database": "spec_labos",
            },
            "runtime": {
                "sim_mode": True,
                "status_poll_interval_seconds": 10,
                "runner_interval_seconds": 1,
            },
            "devices": {
                "enabled_keys": ["nmr_2278"],
            },
        }
    )
    monkeypatch.setattr(main, "get_settings", lambda: settings)

    application = main.create_app()

    assert application.title == "SpecLabOS Test"
