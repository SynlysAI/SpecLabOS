"""设备日志相关 Schema。"""

from pydantic import BaseModel, Field


class DeviceLogFileItem(BaseModel):
    """数据中心日志文件项。"""

    file_id: str
    filename: str = ""
    device_id: str = ""
    collector_id: str = ""
    watcher_name: str = ""
    relative_path: str = ""
    content_type: str = ""
    file_size: int = 0
    ingested_at: str = ""
    created_at: str = ""


class DeviceLogFileListResponse(BaseModel):
    """日志文件列表响应。"""

    items: list[DeviceLogFileItem] = Field(default_factory=list)
    total: int = 0


class DeviceLogContentResponse(BaseModel):
    """日志文件内容响应。"""

    file_id: str
    filename: str = ""
    device_id: str = ""
    content_type: str = ""
    file_size: int = 0
    truncated: bool = False
    content: str = ""
