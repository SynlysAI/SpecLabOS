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
apis: {}
runtime:
  sim_mode: true
  status_poll_interval_seconds: 10
  runner_interval_seconds: 1
datahub:
  api_token: dev-datahub-token
  database: speclabos_data
""".strip(),
        encoding="utf-8",
    )
    devices_config_dir = tmp_path / "config"
    devices_config_dir.mkdir()
    (devices_config_dir / "devices.yaml").write_text(
        """
devices:
  items:
    ir_2278:
      enabled: false
    raman_2278:
      endpoints:
        capture: http://47.113.220.254:7001
        result: http://47.113.220.254:7002
      status_endpoints: [capture, result]
""".strip(),
        encoding="utf-8",
    )

    settings = load_settings(config_file)

    assert isinstance(settings, Settings)
    assert settings.mongo.database == "spec_labos"
    assert settings.rabbitmq.host == "100.84.59.58"
    assert settings.apis.nmr.base_url == ""
    assert settings.apis.raman.result_base_url == ""
    assert settings.device_images.image_dir == str((tmp_path / "images").resolve())
    assert settings.datahub.database == "speclabos_data"
    assert settings.runtime.sim_mode is True
    assert settings.devices.items["ir_2278"].enabled is False
    assert settings.devices.items["raman_2278"].endpoints["capture"] == "http://47.113.220.254:7001"


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
                "items": {
                    "ir_2278": {"enabled": False},
                },
            },
        }
    )
    monkeypatch.setattr(main, "get_settings", lambda: settings)

    application = main.create_app()

    assert application.title == "SpecLabOS Test"


def _write_override_test_config(tmp_path: Path) -> Path:
    """写入用于环境变量覆盖测试的最小配置文件。"""
    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        """
app:
  name: SpecLabOS
  host: 127.0.0.1
  port: 8000
mongo:
  uri: mongodb://yaml-user:yaml-pass@127.0.0.1:27018
  database: spectrum_alab
auth:
  enabled: true
  secret: yaml-secret
  user_mongo_uri: mongodb://yaml-user:yaml-pass@127.0.0.1:27018/ai4ms
  user_database: ai4ms
minio:
  endpoint: 127.0.0.1:9000
  access_key: yaml-access
  secret_key: yaml-minio-secret
rabbitmq:
  host: 127.0.0.1
  port: 5672
  username: yaml-mq-user
  password: yaml-mq-pass
runtime:
  sim_mode: true
llm:
  api_key: yaml-llm-key
  base_url: http://yaml-llm/v1
  model: test-model
external_api:
  api_token: yaml-external-token
""".strip(),
        encoding="utf-8",
    )
    return config_file


def test_env_overrides_take_precedence(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """验证注入的环境变量覆盖 yaml 敏感字段，未覆盖字段保持 yaml 值。"""
    config_file = _write_override_test_config(tmp_path)

    monkeypatch.setenv("AUTH_SECRET", "env-secret")
    monkeypatch.setenv("MONGODB_URI", "mongodb://env-user:env-pass@127.0.0.1:29000/ai4ms")
    monkeypatch.setenv("MINIO_SECRET_KEY", "env-minio-secret")
    monkeypatch.setenv("RABBITMQ_PASSWORD", "env-mq-pass")
    monkeypatch.setenv("LLM_API_KEY", "env-llm-key")
    monkeypatch.setenv("SPECLABOS_API_KEY", "env-external-token")

    settings = load_settings(config_file)

    assert settings.auth.secret == "env-secret"
    assert settings.mongo.uri == "mongodb://env-user:env-pass@127.0.0.1:29000/ai4ms"
    assert settings.auth.user_mongo_uri == settings.mongo.uri
    assert settings.minio.secret_key == "env-minio-secret"
    assert settings.rabbitmq.password == "env-mq-pass"
    assert settings.llm.api_key == "env-llm-key"
    assert settings.external_api.api_token == "env-external-token"
    # 未被覆盖的字段仍来自 yaml
    assert settings.minio.endpoint == "127.0.0.1:9000"
    assert settings.minio.access_key == "yaml-access"
    assert settings.rabbitmq.username == "yaml-mq-user"


def test_env_absent_keeps_yaml_values(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """验证未注入环境变量时完全使用 yaml 值（本地开发场景）。"""
    config_file = _write_override_test_config(tmp_path)

    for env_name in (
        "AUTH_SECRET",
        "MONGODB_URI",
        "MINIO_ACCESS_KEY",
        "MINIO_SECRET_KEY",
        "LLM_API_KEY",
        "RABBITMQ_USERNAME",
        "RABBITMQ_PASSWORD",
        "SPECLABOS_API_KEY",
    ):
        monkeypatch.delenv(env_name, raising=False)

    settings = load_settings(config_file)

    assert settings.auth.secret == "yaml-secret"
    assert settings.mongo.uri == "mongodb://yaml-user:yaml-pass@127.0.0.1:27018"
    assert settings.auth.user_mongo_uri.endswith("/ai4ms")
    assert settings.minio.secret_key == "yaml-minio-secret"
    assert settings.llm.api_key == "yaml-llm-key"
    assert settings.external_api.api_token == "yaml-external-token"
