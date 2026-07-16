"""SmartDataHub 数据资产 Schema。"""

from typing import Any

from pydantic import BaseModel, Field


class DataAssetFileItem(BaseModel):
    """数据资产文件项。"""

    file_id: str
    file_key: str = ""
    asset_id: str
    device_id: str
    collector_id: str
    asset_group_id: str
    root_name: str
    relative_path: str
    filename: str
    content_type: str = ""
    file_size: int = 0
    file_hash: str = ""
    storage_backend: str = "minio"
    storage_bucket: str = ""
    storage_key: str = ""
    storage_uri: str = ""
    upload_status: str = "pending"
    created_at: str = ""
    ingested_at: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)


class DataAssetItem(BaseModel):
    """数据资产项。"""

    asset_id: str
    asset_key: str = ""
    asset_kind: str = "file"
    asset_group_id: str = ""
    device_id: str = ""
    collector_id: str = ""
    data_type: str = ""
    root_name: str = ""
    filename: str = ""
    file_count: int = 1
    total_size: int = 0
    file_hash: str = ""
    storage_backend: str = "minio"
    storage_bucket: str = ""
    storage_prefix: str = ""
    storage_uri: str = ""
    upload_status: str = "pending"
    created_at: str = ""
    ingested_at: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)


class DataAssetDistributionItem(BaseModel):
    """数据资产分布项。"""

    key: str = ""
    label: str = ""
    asset_count: int = 0
    file_count: int = 0
    total_size: int = 0
    latest_ingested_at: str = ""


class DataAssetListResponse(BaseModel):
    """数据资产列表响应。"""

    items: list[DataAssetItem] = Field(default_factory=list)
    total: int = 0


class DataAssetOverviewResponse(BaseModel):
    """数据资产概览响应。"""

    asset_count: int = 0
    file_count: int = 0
    total_size: int = 0
    device_count: int = 0
    collector_count: int = 0
    latest_ingested_at: str = ""
    data_type_distribution: list[DataAssetDistributionItem] = Field(default_factory=list)
    device_distribution: list[DataAssetDistributionItem] = Field(default_factory=list)
    collector_distribution: list[DataAssetDistributionItem] = Field(default_factory=list)


class DataAssetFileListResponse(BaseModel):
    """数据资产文件列表响应。"""

    items: list[DataAssetFileItem] = Field(default_factory=list)


class DataIngestFileResponse(BaseModel):
    """文件上传响应。"""

    asset_id: str
    file_id: str
    storage_bucket: str
    storage_key: str
    storage_uri: str
    upload_status: str = "completed"
