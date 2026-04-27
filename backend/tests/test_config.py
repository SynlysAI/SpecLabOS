"""配置加载测试。"""

from pathlib import Path

from app.core.config import Settings, load_settings


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
