"""应用配置加载模块。"""

from functools import lru_cache
from pathlib import Path

import yaml
from pydantic import BaseModel, Field


class AppSettings(BaseModel):
    """应用基础配置。"""

    name: str = "SpecLabOS"
    host: str = "127.0.0.1"
    port: int = 8000


class MongoSettings(BaseModel):
    """MongoDB 连接配置。"""

    uri: str
    database: str = "spec_labos"


class RuntimeSettings(BaseModel):
    """运行时参数配置。"""

    sim_mode: bool = True
    status_poll_interval_seconds: int = 10
    runner_interval_seconds: int = 1


class DeviceSettings(BaseModel):
    """设备启用配置。"""

    enabled_keys: list[str] = Field(default_factory=list)


class Settings(BaseModel):
    """系统总配置。"""

    app: AppSettings
    mongo: MongoSettings
    runtime: RuntimeSettings
    devices: DeviceSettings


def get_default_config_path(current_file: str | Path | None = None) -> Path:
    """解析默认配置文件路径。

    Args:
        current_file: 当前模块文件路径，默认使用当前文件。

    Returns:
        项目根目录下的配置文件路径。
    """
    config_module_file = Path(current_file or __file__).resolve()
    backend_root = config_module_file.parents[2]
    project_root = backend_root.parent
    return project_root / "config.yaml"


def load_settings(config_path: str | Path) -> Settings:
    """从 YAML 文件加载系统配置。

    Args:
        config_path: 配置文件路径。

    Returns:
        解析后的系统配置对象。
    """
    config_file = Path(config_path)
    raw_data = yaml.safe_load(config_file.read_text(encoding="utf-8"))
    return Settings.model_validate(raw_data)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """读取并缓存项目根目录下的默认配置。"""
    return load_settings(get_default_config_path())
