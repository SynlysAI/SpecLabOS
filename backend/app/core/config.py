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


class MinioSettings(BaseModel):
    """MinIO 对象存储配置。"""

    endpoint: str = "127.0.0.1:9000"
    access_key: str = "minioadmin"
    secret_key: str = "minioadmin"
    bucket: str = "speclabos-data"
    secure: bool = False


class DataHubSettings(BaseModel):
    """SmartDataHub 上传接口配置。"""

    api_token: str = ""
    database: str = "speclabos_data"


class AuthSettings(BaseModel):
    """统一认证配置。"""

    enabled: bool = True
    token_expire_hours: int = 12
    secret: str = ""
    user_mongo_uri: str = ""
    user_database: str = "ai4ms"


class SmartAccessSettings(BaseModel):
    """SmartAccess 接入配置。"""

    api_token: str = ""


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


class SciverseApiSettings(BaseModel):
    """Sciverse 科学文献检索 API 配置。"""

    base_url: str = "https://api.sciverse.space"
    api_token: str = ""
    timeout: int = 30


class DianshiApiSettings(BaseModel):
    """点石化学信息检索 MCP 配置。"""

    mcp_url: str = "https://dianshi.opendatalab.com/api/mcp"
    api_token: str = ""
    timeout: int = 30


class ApiSettings(BaseModel):
    """外部设备接口配置。"""

    sciverse: SciverseApiSettings = Field(default_factory=SciverseApiSettings)
    dianshi: DianshiApiSettings = Field(default_factory=DianshiApiSettings)
    gpc: ApiEndpointSettings = Field(default_factory=ApiEndpointSettings)
    resin: ResinApiSettings = Field(default_factory=ResinApiSettings)
    station: ApiEndpointSettings = Field(default_factory=ApiEndpointSettings)
    pi: ApiEndpointSettings = Field(default_factory=ApiEndpointSettings)
    nmr: ApiEndpointSettings = Field(default_factory=ApiEndpointSettings)
    raman: RamanApiSettings = Field(default_factory=RamanApiSettings)
    lcms: ApiEndpointSettings = Field(default_factory=ApiEndpointSettings)


class RuntimeSettings(BaseModel):
    """运行时参数配置。"""

    sim_mode: bool = True
    status_poll_interval_seconds: int = 10
    runner_interval_seconds: int = 1


class DeviceItemSettings(BaseModel):
    """单台设备实例配置。"""

    enabled: bool | None = None
    image: str = ""
    endpoints: dict[str, str] = Field(default_factory=dict)
    status_endpoints: list[str] = Field(default_factory=list)
    status_timeout_seconds: float | None = None
    health_path: str = ""
    health_device: str = ""


class DeviceSettings(BaseModel):
    """设备实例配置。"""

    disabled_keys: list[str] = Field(default_factory=list)
    items: dict[str, DeviceItemSettings] = Field(default_factory=dict)


class LlmSettings(BaseModel):
    """LLM 大模型接口配置。"""

    api_key: str = ""
    base_url: str = "https://api.openai.com/v1"
    model: str = "gpt-3.5-turbo"


class Settings(BaseModel):
    """系统总配置。"""

    app: AppSettings
    mongo: MongoSettings
    minio: MinioSettings = Field(default_factory=MinioSettings)
    datahub: DataHubSettings = Field(default_factory=DataHubSettings)
    auth: AuthSettings = Field(default_factory=AuthSettings)
    smartaccess: SmartAccessSettings = Field(default_factory=SmartAccessSettings)
    rabbitmq: RabbitMQSettings = Field(default_factory=RabbitMQSettings)
    device_images: DeviceImagesSettings = Field(default_factory=DeviceImagesSettings)
    device_logs: DeviceLogSettings = Field(default_factory=DeviceLogSettings)
    apis: ApiSettings = Field(default_factory=ApiSettings)
    runtime: RuntimeSettings
    devices: DeviceSettings = Field(default_factory=DeviceSettings)
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


def _resolve_config_relative_path(path_value: str, config_file: Path) -> str:
    """将配置中的相对路径解析为相对配置文件所在目录的绝对路径。

    Args:
        path_value: 配置中的路径文本。
        config_file: 配置文件路径。

    Returns:
        解析后的路径文本。
    """
    target_path = Path(path_value)
    if target_path.is_absolute():
        return str(target_path)
    return str((config_file.parent / target_path).resolve())


def _resolve_device_image_dir(raw_data: dict, config_file: Path) -> None:
    """解析设备图片目录配置。

    Args:
        raw_data: 原始配置数据。
        config_file: 配置文件路径。
    """
    device_images = raw_data.get("device_images")
    if not isinstance(device_images, dict):
        return

    image_dir = device_images.get("image_dir")
    if isinstance(image_dir, str) and image_dir:
        device_images["image_dir"] = _resolve_config_relative_path(
            image_dir,
            config_file,
        )


def get_default_devices_config_path(config_file: Path) -> Path:
    """获取默认设备实例配置文件路径。

    Args:
        config_file: 主配置文件路径。

    Returns:
        默认设备实例配置文件路径。
    """
    return config_file.parent / "config" / "devices.yaml"


def _load_devices_config(config_file: Path) -> dict:
    """加载独立设备实例配置。

    Args:
        config_file: 主配置文件路径。

    Returns:
        设备实例配置字典，不存在时返回空字典。
    """
    devices_config_file = get_default_devices_config_path(config_file)
    if not devices_config_file.is_file():
        return {}
    raw_devices = yaml.safe_load(devices_config_file.read_text(encoding="utf-8"))
    if not isinstance(raw_devices, dict):
        return {}
    return raw_devices.get("devices", raw_devices)


def _merge_devices_config(raw_data: dict, config_file: Path) -> None:
    """合并主配置与独立设备实例配置。

    Args:
        raw_data: 原始主配置数据。
        config_file: 主配置文件路径。
    """
    devices_config = _load_devices_config(config_file)
    if not devices_config:
        return
    main_devices = raw_data.get("devices")
    if not isinstance(main_devices, dict):
        raw_data["devices"] = devices_config
        return
    merged_devices = {**main_devices, **devices_config}
    merged_devices["items"] = {
        **main_devices.get("items", {}),
        **devices_config.get("items", {}),
    }
    raw_data["devices"] = merged_devices


def load_settings(config_path: str | Path) -> Settings:
    """从 YAML 文件加载系统配置。

    Args:
        config_path: 配置文件路径。

    Returns:
        解析后的系统配置对象。
    """
    config_file = Path(config_path).resolve()
    raw_data = yaml.safe_load(config_file.read_text(encoding="utf-8"))
    if isinstance(raw_data, dict):
        _resolve_device_image_dir(raw_data, config_file)
        _merge_devices_config(raw_data, config_file)
    return Settings.model_validate(raw_data)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """读取并缓存项目根目录下的默认配置。"""
    return load_settings(get_default_config_path())
