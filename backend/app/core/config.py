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
    completed_uri: str = ""
    completed_database: str = ""


class RabbitMQSettings(BaseModel):
    """RabbitMQ 连接配置。"""

    host: str = "127.0.0.1"
    port: int = 5672
    username: str = "guest"
    password: str = "guest"


class DeviceImagesSettings(BaseModel):
    """设备图片目录配置。"""

    image_dir: str = ""


class DeviceLogSettings(BaseModel):
    """设备日志目录配置。"""

    raman_dir: str = ""
    gpc_lcms_dir: str = ""
    nmr_dir: str = ""
    gpc_rate_csv: str = ""
    lcms_rate_csv: str = ""
    nmr_rate_csv: str = ""
    raman_window_days: int = 3


class ApiEndpointSettings(BaseModel):
    """通用接口地址配置。"""

    base_url: str = ""
    timeout: int = 30


class ResinApiSettings(ApiEndpointSettings):
    """Resin 接口配置。"""

    devices: dict[str, str] = Field(default_factory=dict)


class RamanApiSettings(BaseModel):
    """Raman 接口配置。"""

    capture_base_url: str = ""
    result_base_url: str = ""
    timeout: int = 60


class ApiSettings(BaseModel):
    """外部设备接口配置。"""

    gpc: ApiEndpointSettings = Field(default_factory=ApiEndpointSettings)
    resin: ResinApiSettings = Field(default_factory=ResinApiSettings)
    station: ApiEndpointSettings = Field(default_factory=ApiEndpointSettings)
    pi: ApiEndpointSettings = Field(default_factory=ApiEndpointSettings)
    nmr: ApiEndpointSettings = Field(default_factory=ApiEndpointSettings)
    raman: RamanApiSettings = Field(default_factory=RamanApiSettings)


class RuntimeSettings(BaseModel):
    """运行时参数配置。"""

    sim_mode: bool = True
    status_poll_interval_seconds: int = 10
    runner_interval_seconds: int = 1


class DeviceSettings(BaseModel):
    """设备启用配置。"""

    enabled_keys: list[str] = Field(default_factory=list)


class LlmSettings(BaseModel):
    """LLM 大模型接口配置。"""

    api_key: str = ""
    base_url: str = "https://api.openai.com/v1"
    model: str = "gpt-3.5-turbo"


class Settings(BaseModel):
    """系统总配置。"""

    app: AppSettings
    mongo: MongoSettings
    rabbitmq: RabbitMQSettings = Field(default_factory=RabbitMQSettings)
    device_images: DeviceImagesSettings = Field(default_factory=DeviceImagesSettings)
    device_logs: DeviceLogSettings = Field(default_factory=DeviceLogSettings)
    apis: ApiSettings = Field(default_factory=ApiSettings)
    runtime: RuntimeSettings
    devices: DeviceSettings
    llm: LlmSettings = Field(default_factory=LlmSettings)


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
