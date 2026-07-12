"""数据采集策略领域模型。"""

from pydantic import BaseModel, Field


class DataCollectionPolicy(BaseModel):
    """数据采集策略。

    描述设备产出数据的采集方式、存储目标和元数据关联。
    阶段 1 仅定义模型，实际实现在阶段 3（SmartDataHub MVP）。
    """

    policy_id: str
    device_id: str
    source_type: str
    source_path: str | None = None
    file_patterns: list[str] = Field(default_factory=list)
    upload_target: str = "minio"
    metadata_fields: list[str] = Field(default_factory=list)
    bind_run_id: bool = True
