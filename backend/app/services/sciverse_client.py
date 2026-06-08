"""Sciverse 科学文献检索 REST API 客户端。"""

import logging

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from app.core.config import get_settings

_logger = logging.getLogger(__name__)


def _get_session() -> requests.Session:
    """创建带重试策略的 HTTP 会话。

    Returns:
        配置了超时和重试的 requests Session。
    """
    settings = get_settings().apis.sciverse
    session = requests.Session()
    session.headers.update({
        "Authorization": f"Bearer {settings.api_token}",
        "Content-Type": "application/json",
    })
    retries = Retry(
        total=2,
        backoff_factor=0.5,
        status_forcelist=[500, 502, 503, 504],
        allowed_methods=["GET", "POST"],
    )
    session.mount("https://", HTTPAdapter(max_retries=retries))
    return session


def _base_url() -> str:
    return get_settings().apis.sciverse.base_url


def agentic_search(query: str, top_k: int = 10, sub_queries: int = 0) -> dict:
    """智能检索文献片段。

    Args:
        query: 自然语言检索问题，最长 4096 字符。
        top_k: 返回片段数量，1–100，默认 10。
        sub_queries: 查询改写数量，0–4，默认 0。

    Returns:
        包含 hits 列表的响应字典。
    """
    session = _get_session()
    resp = session.post(
        f"{_base_url()}/agentic-search",
        json={"query": query, "top_k": top_k, "sub_queries": sub_queries},
        timeout=get_settings().apis.sciverse.timeout,
    )
    resp.raise_for_status()
    return resp.json()


def get_content(doc_id: str, offset: int | None = None, limit: int = 700) -> dict:
    """按 doc_id 分段读取文献全文。

    Args:
        doc_id: 文献 ID（由 agentic-search 或 meta-search 返回）。
        offset: 字符偏移，不传则返回全文。
        limit: 单次最大字符数，默认 700，仅在传入 offset 时生效。

    Returns:
        包含 text、next_offset、more 等字段的字典。
    """
    session = _get_session()
    params = {"doc_id": doc_id}
    if offset is not None:
        params["offset"] = offset
        params["limit"] = limit
    resp = session.get(
        f"{_base_url()}/content",
        params=params,
        timeout=get_settings().apis.sciverse.timeout,
    )
    resp.raise_for_status()
    return resp.json()


def get_resource(file_name: str) -> bytes:
    """按相对路径下载文献附件。

    Args:
        file_name: 资源相对路径，不得包含 \\、..、/ 开头。

    Returns:
        二进制文件内容。
    """
    session = _get_session()
    resp = session.get(
        f"{_base_url()}/resource",
        params={"file_name": file_name},
        timeout=get_settings().apis.sciverse.timeout,
    )
    resp.raise_for_status()
    return resp.content


def meta_catalog(include_sample_values: bool = False) -> dict:
    """查看 meta-search 支持的字段目录。

    Args:
        include_sample_values: 是否返回枚举字段样本值，缓存 24 小时。

    Returns:
        包含 fields 列表的响应字典。
    """
    session = _get_session()
    resp = session.get(
        f"{_base_url()}/meta-catalog",
        params={"include_sample_values": include_sample_values},
        timeout=get_settings().apis.sciverse.timeout,
    )
    resp.raise_for_status()
    return resp.json()


def meta_search(
    query: str | None = None,
    filters: list[dict] | None = None,
    sort: list[dict] | None = None,
    fields: list[str] | None = None,
    page: int = 1,
    page_size: int = 25,
    cursor: str | None = None,
    freshness_boost: str | None = None,
) -> dict:
    """按结构化条件检索文献元数据。

    Args:
        query: 全文模糊检索词，与 sort 互斥。
        filters: 字段过滤条件列表，每项 {field, operator?, value}。
        sort: 排序字段集合，每项 {field, order}。
        fields: 字段投影列表。
        page: 页码，≥1。
        page_size: 每页条数，1–200，默认 25。
        cursor: 游标翻页令牌，与 page>1 互斥。
        freshness_boost: 新鲜度加权，NONE/MILD/STRONG。

    Returns:
        包含 results、total_count、next_cursor 等的响应字典。
    """
    session = _get_session()
    body = {}
    if query is not None:
        body["query"] = query
    if filters is not None:
        body["filters"] = filters
    if sort is not None:
        body["sort"] = sort
    if fields is not None:
        body["fields"] = fields
    if cursor is not None:
        body["cursor"] = cursor
    else:
        body["page"] = page
        body["page_size"] = page_size
    if freshness_boost is not None:
        body["freshness_boost"] = freshness_boost

    resp = session.post(
        f"{_base_url()}/meta-search",
        json=body,
        timeout=get_settings().apis.sciverse.timeout,
    )
    resp.raise_for_status()
    return resp.json()
