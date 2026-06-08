"""点石 DianShi MCP 客户端 — 基于 JSON-RPC over Streamable HTTP。"""

import logging
import uuid

import requests

from app.core.config import get_settings

_logger = logging.getLogger(__name__)

# 14 个 MCP 工具的参数定义（用于 LLM function calling）
DIANSHI_TOOLS = [
    {
        "name": "substance_get_by_id",
        "description": "按 ID 获取化学物质详情（inchi_key、SMILES、分子式、分子量、IUPAC 名称等）。",
        "parameters": {
            "type": "object",
            "properties": {
                "substance_id": {"type": "string", "description": "物质 ID（CUID 格式）"},
            },
            "required": ["substance_id"],
        },
    },
    {
        "name": "substance_search",
        "description": "按名称/SMILES/InChIKey 搜索化学物质，结果按关联文献数降序排列。",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "搜索词（名称、SMILES、InChIKey 或同义词）"},
                "limit": {"type": "integer", "description": "最大结果数，默认 20，范围 1–100"},
                "offset": {"type": "integer", "description": "分页偏移量，默认 0"},
            },
            "required": ["query"],
        },
    },
    {
        "name": "substance_similarity",
        "description": "Morgan 指纹 Tanimoto 相似度搜索，覆盖 630 万物质，按相似度降序。",
        "parameters": {
            "type": "object",
            "properties": {
                "smiles": {"type": "string", "description": "查询分子的 SMILES"},
                "threshold": {"type": "number", "description": "最低 Tanimoto 相似度，默认 0.5，范围 0.0–1.0"},
                "limit": {"type": "integer", "description": "最大结果数，默认 20，范围 1–100"},
            },
            "required": ["smiles"],
        },
    },
    {
        "name": "substance_substructure",
        "description": "子结构搜索，支持 SMILES 和 SMARTS 查询。",
        "parameters": {
            "type": "object",
            "properties": {
                "smiles": {"type": "string", "description": "子结构查询（SMILES 或 SMARTS）"},
                "limit": {"type": "integer", "description": "最大结果数，默认 20，范围 1–100"},
            },
            "required": ["smiles"],
        },
    },
    {
        "name": "reaction_search",
        "description": "按反应 SMILES 子串搜索反应组，按实例数降序。",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "反应 SMILES 子串"},
                "limit": {"type": "integer", "description": "最大结果数，默认 20，范围 1–100"},
                "offset": {"type": "integer", "description": "分页偏移量，默认 0"},
            },
            "required": ["query"],
        },
    },
    {
        "name": "reaction_get_by_hash",
        "description": "按反应哈希（SHA-256）获取反应组详情及代表实例。",
        "parameters": {
            "type": "object",
            "properties": {
                "reaction_hash": {"type": "string", "description": "反应组哈希（SHA-256）"},
            },
            "required": ["reaction_hash"],
        },
    },
    {
        "name": "reaction_conditions",
        "description": "获取指定反应组的聚合条件信息（溶剂、催化剂、试剂、产率等，最多 20 个实例）。",
        "parameters": {
            "type": "object",
            "properties": {
                "reaction_hash": {"type": "string", "description": "反应组哈希"},
            },
            "required": ["reaction_hash"],
        },
    },
    {
        "name": "reaction_by_product",
        "description": "基于产物 Morgan 指纹相似度搜索反应，用于逆合成路线发现。",
        "parameters": {
            "type": "object",
            "properties": {
                "smiles": {"type": "string", "description": "目标产物 SMILES"},
                "threshold": {"type": "number", "description": "最低相似度，默认 0.5，范围 0.0–1.0"},
                "limit": {"type": "integer", "description": "最大结果数，默认 20，范围 1–100"},
            },
            "required": ["smiles"],
        },
    },
    {
        "name": "reaction_similar_struct",
        "description": "AtomPair 结构指纹反应相似度检索，适合快速筛选相似反应。",
        "parameters": {
            "type": "object",
            "properties": {
                "rxn_smiles": {"type": "string", "description": "查询反应 SMILES"},
                "threshold": {"type": "number", "description": "最低相似度，默认 0.4，范围 0.0–1.0"},
                "limit": {"type": "integer", "description": "最大结果数，默认 20，范围 1–100"},
            },
            "required": ["rxn_smiles"],
        },
    },
    {
        "name": "reaction_similar_diff_bfp",
        "description": "AtomPair 差异指纹反应相似度检索，低延迟（~150ms），适合实时场景。",
        "parameters": {
            "type": "object",
            "properties": {
                "rxn_smiles": {"type": "string", "description": "查询反应 SMILES"},
                "threshold": {"type": "number", "description": "最低相似度，默认 0.3，范围 0.0–1.0"},
                "limit": {"type": "integer", "description": "最大结果数，默认 20，范围 1–100"},
            },
            "required": ["rxn_smiles"],
        },
    },
    {
        "name": "reaction_similar_diff_morgan",
        "description": "Morgan 差异指纹反应相似度检索，精度高但耗时较长（~13s）。对延迟敏感请用 reaction_similar_diff_bfp。",
        "parameters": {
            "type": "object",
            "properties": {
                "rxn_smiles": {"type": "string", "description": "查询反应 SMILES"},
                "threshold": {"type": "number", "description": "最低相似度（sfp 范围），默认 0.3，范围 -1.0–1.0"},
                "limit": {"type": "integer", "description": "最大结果数，默认 20，范围 1–100"},
            },
            "required": ["rxn_smiles"],
        },
    },
    {
        "name": "reference_get_by_id",
        "description": "按 ID 获取化学专利/文献详情（标题、DOI、作者、摘要、分类号等）。",
        "parameters": {
            "type": "object",
            "properties": {
                "reference_id": {"type": "string", "description": "文献 ID（CUID 格式）"},
            },
            "required": ["reference_id"],
        },
    },
    {
        "name": "reference_search",
        "description": "化学专利与文献全文检索，按相关度排序。",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "搜索关键词"},
                "limit": {"type": "integer", "description": "最大结果数，默认 20，范围 1–100"},
                "offset": {"type": "integer", "description": "分页偏移量，默认 0"},
            },
            "required": ["query"],
        },
    },
    {
        "name": "health_check",
        "description": "检查点石数据库连通性，返回核心表行数统计。",
        "parameters": {
            "type": "object",
            "properties": {},
        },
    },
]


def _mcp_url() -> str:
    return get_settings().apis.dianshi.mcp_url


def _token() -> str:
    return get_settings().apis.dianshi.api_token


def _rpc_call(method: str, params: dict | None = None) -> dict:
    """发送 JSON-RPC 请求到点石 MCP 端点。

    Args:
        method: JSON-RPC 方法名（如 tools/call）。
        params: 方法参数字典。

    Returns:
        JSON-RPC 响应的 result 字段。

    Raises:
        RuntimeError: MCP 调用返回错误或 HTTP 异常。
    """
    payload = {
        "jsonrpc": "2.0",
        "id": str(uuid.uuid4()),
        "method": method,
        "params": params or {},
    }
    settings = get_settings().apis.dianshi
    try:
        resp = requests.post(
            settings.mcp_url,
            json=payload,
            headers={
                "Authorization": f"Bearer {settings.api_token}",
                "Content-Type": "application/json",
            },
            timeout=settings.timeout,
        )
        resp.raise_for_status()
        data = resp.json()
    except requests.exceptions.SSLError as exc:
        _logger.exception("MCP SSL 连接失败")
        raise RuntimeError(
            f"点石服务 SSL 连接失败，服务器 TLS 可能异常。"
            f"请确认 {settings.mcp_url} 可正常访问后重试。"
        ) from exc
    except requests.RequestException as exc:
        _logger.exception("MCP HTTP 调用失败: %s", method)
        raise RuntimeError(f"点石服务请求失败: {exc}") from exc

    if "error" in data:
        err = data["error"]
        raise RuntimeError(f"MCP 错误 [{err.get('code')}]: {err.get('message', str(err))}")

    return data.get("result", data)


def check_available() -> bool:
    """检查点石 MCP 服务是否可用。

    Returns:
        True 表示服务可用，False 表示未启用或不可达。
    """
    try:
        _rpc_call("tools/list")
        return True
    except RuntimeError:
        return False


def call_tool(name: str, arguments: dict) -> dict:
    """调用指定 MCP 工具。

    Args:
        name: 工具名称。
        arguments: 工具参数字典。

    Returns:
        工具执行结果的 content 列表中的 text。出错返回 isError 信息。
    """
    result = _rpc_call("tools/call", {"name": name, "arguments": arguments})
    content = result.get("content", [])
    if result.get("isError"):
        error_text = "".join(
            c.get("text", "") for c in content if c.get("type") == "text"
        )
        _logger.warning("MCP 工具 %s 返回错误: %s", name, error_text)
        return {"error": True, "message": error_text or "未知 MCP 工具错误"}
    return result
