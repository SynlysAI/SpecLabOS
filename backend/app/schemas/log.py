"""日志相关 Schema。"""

from pydantic import BaseModel, Field


class LogItem(BaseModel):
    """日志列表项。"""

    id: str
    level: str
    message: str
    source: str = "system"
    source_label: str = "System"
    service_name: str = "system"
    created_at: str = "--"
    file_path: str = ""
    raw_content: str = ""


class LogListResponse(BaseModel):
    """日志列表响应。"""

    items: list[LogItem] = Field(default_factory=list)
