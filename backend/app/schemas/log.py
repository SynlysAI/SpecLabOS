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


class AutomationRateMetric(BaseModel):
    """单个设备自动化率指标。"""

    key: str
    label: str
    rate: float = 0.0
    sample_count: int = 0
    completed_count: int = 0
    source_type: str = ""
    description: str = ""


class AutomationRateSummaryResponse(BaseModel):
    """自动化率摘要响应。"""

    overall_rate: float = 0.0
    metrics: list[AutomationRateMetric] = Field(default_factory=list)
