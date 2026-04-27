"""日志相关 Schema。"""

from pydantic import BaseModel, Field


class LogItem(BaseModel):
    """日志列表项。"""

    level: str
    message: str
    source: str = "system"


class LogListResponse(BaseModel):
    """日志列表响应。"""

    items: list[LogItem] = Field(default_factory=list)
