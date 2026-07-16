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
rabbitmq:
  host: 100.84.59.58
  port: 5672
  username: admin
  password: password123
device_images:
  image_dir: images
apis:
  gpc:
    base_url: http://100.74.253.59:8001
  resin:
    base_url: http://47.113.220.254:7000
    devices:
      resin_2278: http://47.113.220.254:7000
      resin_2278_2: http://47.113.220.254:7000
      resin_1438: http://47.113.220.254:7000
  station:
    base_url: http://47.113.220.254:7001
  pi:
    base_url: http://47.113.220.254:6667
  nmr:
    base_url: http://127.0.0.1:18080
    timeout: 60
  raman:
    capture_base_url: http://47.113.220.254:7001
    result_base_url: http://47.113.220.254:7002
    timeout: 60
runtime:
  sim_mode: true
  status_poll_interval_seconds: 10
  runner_interval_seconds: 1
devices:
  disabled_keys: [ir_2278]
datahub:
  api_token: dev-datahub-token
  database: speclabos_data
""".strip(),
        encoding="utf-8",
    )

    settings = load_settings(config_file)

    assert isinstance(settings, Settings)
    assert settings.mongo.database == "spec_labos"
    assert settings.rabbitmq.host == "100.84.59.58"
    assert settings.apis.nmr.base_url == "http://127.0.0.1:18080"
    assert settings.apis.raman.result_base_url == "http://47.113.220.254:7002"
    assert settings.device_images.image_dir == str((tmp_path / "images").resolve())
    assert settings.datahub.database == "speclabos_data"
    assert settings.runtime.sim_mode is True
    assert settings.devices.disabled_keys == ["ir_2278"]


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
            "datahub": {
                "api_token": "dev-datahub-token",
                "database": "speclabos_data",
            },
            "rabbitmq": {
                "host": "100.84.59.58",
                "port": 5672,
                "username": "admin",
                "password": "password123",
            },
            "device_images": {
                "image_dir": "E:/github_project/SpecLabOS/examples/spectrum_alab/alabos_project/images",
            },
            "apis": {
                "gpc": {"base_url": "http://100.74.253.59:8001"},
                "resin": {
                    "base_url": "http://47.113.220.254:7000",
                    "devices": {
                        "resin_2278": "http://47.113.220.254:7000",
                    },
                },
                "station": {"base_url": "http://47.113.220.254:7001"},
                "pi": {"base_url": "http://47.113.220.254:6667"},
                "nmr": {"base_url": "http://127.0.0.1:18080", "timeout": 60},
                "raman": {
                    "capture_base_url": "http://47.113.220.254:7001",
                    "result_base_url": "http://47.113.220.254:7002",
                    "timeout": 60,
                },
            },
            "runtime": {
                "sim_mode": True,
                "status_poll_interval_seconds": 10,
                "runner_interval_seconds": 1,
            },
            "devices": {
                "disabled_keys": ["ir_2278"],
            },
        }
    )
    monkeypatch.setattr(main, "get_settings", lambda: settings)

    application = main.create_app()

    assert application.title == "SpecLabOS Test"
