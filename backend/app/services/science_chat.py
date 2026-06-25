"""科学数据助手对话服务 — LLM 工具调用路由 + SSE 流式响应生成。"""

import json
import logging

import requests

from app.core.config import get_settings
from app.services import sciverse_client, dianshi_mcp

_logger = logging.getLogger(__name__)

# ── Sciverse 5 个工具定义 ──────────────────────────────────────
SCIVERSE_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "agentic_search",
            "description": "用自然语言检索科学文献片段。返回标题、正文片段、doc_id、页码/位置和来源类型，适合 RAG、Agent 工具调用、问答系统等场景。",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "自然语言检索问题，最长 4096 字符"},
                    "top_k": {"type": "integer", "description": "返回片段数量，默认 10，范围 1–100"},
                    "sub_queries": {"type": "integer", "description": "查询改写数量，0 表示不改写，范围 0–4，默认 0"},
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "content",
            "description": "按 doc_id 分段读取文献全文（Markdown 或纯文本）。doc_id 来自 agentic_search 或 meta_search 结果。支持 offset/limit 分段拉取以适配长上下文。",
            "parameters": {
                "type": "object",
                "properties": {
                    "doc_id": {"type": "string", "description": "文献 ID"},
                    "offset": {"type": "integer", "description": "字符偏移（Unicode 码点数），不传返回全文"},
                    "limit": {"type": "integer", "description": "单次最大字符数，默认 700"},
                },
                "required": ["doc_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "resource",
            "description": "按相对路径下载论文插图、实验图等二进制附件。file_name 来自检索结果、解析结果或正文中的图片路径，只传相对路径。响应为二进制流。",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_name": {"type": "string", "description": "资源相对路径，如 papers/2025/abcd/fig1.png"},
                },
                "required": ["file_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "meta_catalog",
            "description": "查看 meta_search 支持哪些字段、哪些字段可筛选或排序、默认返回列及过滤算子。适合在搭筛选器或让 Agent 自动拼 meta_search 请求前调用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "include_sample_values": {"type": "boolean", "description": "是否返回枚举字段样本值，默认 false"},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "meta_search",
            "description": "按年份、期刊、DOI、语言等结构化条件筛选文献元数据（标题、摘要、作者等），支持字段过滤、排序、分页、新鲜度加权。不返回段落正文。query 与 sort 不能同时使用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "全文模糊检索词，与 sort 互斥"},
                    "filters": {
                        "type": "array",
                        "description": "字段过滤条件列表，每个条件是包含 field/operator/value 的对象",
                        "items": {
                            "type": "object",
                            "properties": {
                                "field": {"type": "string", "description": "要过滤的字段名，如 publication_published_year"},
                                "operator": {"type": "string", "description": "过滤算子，必须用下划线全称：FILTER_OP_EQ, FILTER_OP_NE, FILTER_OP_GT, FILTER_OP_GTE, FILTER_OP_LT, FILTER_OP_LTE, FILTER_OP_IN, FILTER_OP_NIN, FILTER_OP_CONTAINS"},
                                "value": {"description": "过滤值，年份用整数，其他字段按类型"},
                            },
                            "required": ["field", "value"],
                        },
                    },
                    "sort": {
                        "type": "array",
                        "description": "排序字段集合，每项 {field, order}。与 query 互斥。可排序字段: publication_published_year, citation_count, influential_citation_count, reference_count, fwci",
                        "items": {
                            "type": "object",
                            "properties": {
                                "field": {"type": "string"},
                                "order": {"type": "string", "description": "SORT_ORDER_ASC 或 SORT_ORDER_DESC"},
                            },
                        },
                    },
                    "fields": {"type": "array", "items": {"type": "string"}, "description": "字段投影列表，如 ['title','doi','publication_published_year','citation_count']"},
                    "page": {"type": "integer", "description": "页码，默认 1"},
                    "page_size": {"type": "integer", "description": "每页条数，默认 25，范围 1–200"},
                    "freshness_boost": {"type": "string", "description": "新鲜度加权：NONE / MILD（近10年）/ STRONG（近3年）"},
                },
            },
        },
    },
]


def _wrap_mcp_tools(raw_tools: list[dict]) -> list[dict]:
    """将 MCP 工具定义转换为 OpenAI function calling 格式。

    Args:
        raw_tools: MCP 原生工具定义列表（不含 type/function 包装）。

    Returns:
        OpenAI function calling 格式的工具定义列表。
    """
    return [
        {
            "type": "function",
            "function": {
                "name": t["name"],
                "description": t["description"],
                "parameters": t["parameters"],
            },
        }
        for t in raw_tools
    ]


def _llm_request(messages: list[dict], tools: list[dict] | None = None) -> dict:
    """同步调用 LLM API（OpenAI 兼容接口）。

    Args:
        messages: 对话消息列表。
        tools: 可选工具定义列表。

    Returns:
        API 响应的 JSON 字典。
    """
    llm = get_settings().llm
    body = {
        "model": llm.model,
        "messages": messages,
        "temperature": 0,
        "max_tokens": 4096,
    }
    if tools:
        body["tools"] = tools
        body["tool_choice"] = "auto"

    resp = requests.post(
        f"{llm.base_url}/chat/completions",
        headers={
            "Authorization": f"Bearer {llm.api_key}",
            "Content-Type": "application/json",
        },
        json=body,
        timeout=120,
    )
    resp.raise_for_status()
    return resp.json()


def _llm_stream(messages: list[dict]):
    """流式调用 LLM API，逐行 yield JSON chunk 字符串。

    Args:
        messages: 对话消息列表。
    """
    llm = get_settings().llm
    body = {
        "model": llm.model,
        "messages": messages,
        "temperature": 0,
        "max_tokens": 4096,
        "stream": True,
    }
    resp = requests.post(
        f"{llm.base_url}/chat/completions",
        headers={
            "Authorization": f"Bearer {llm.api_key}",
            "Content-Type": "application/json",
        },
        json=body,
        stream=True,
        timeout=120,
    )
    resp.raise_for_status()
    for line in resp.iter_lines(decode_unicode=True):
        if line and line.startswith("data: "):
            yield line


def _execute_tool(product: str, name: str, arguments: dict) -> str:
    """执行工具调用，返回 JSON 字符串结果。

    Args:
        product: 产品标识，"sciverse" 或 "dianshi"。
        name: 工具/函数名称。
        arguments: 调用参数字典。

    Returns:
        格式化后的 JSON 结果字符串。
    """
    try:
        if product == "sciverse":
            func = getattr(sciverse_client, name)
            result = func(**arguments)
            if isinstance(result, bytes):
                return f"[二进制数据，长度: {len(result)} bytes]"
            return json.dumps(result, ensure_ascii=False, indent=2)
        else:
            result = dianshi_mcp.call_tool(name, arguments)
            if isinstance(result, dict) and result.get("error"):
                return f"[错误] {result['message']}"
            return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as exc:
        _logger.exception("工具 %s/%s 执行失败", product, name)
        detail = str(exc)
        # HTTP 错误时附带 API 返回的具体错误信息，帮助 LLM 修正参数
        if hasattr(exc, "response") and hasattr(exc.response, "text"):
            try:
                detail = f"{exc} | API 返回: {exc.response.text[:500]}"
            except Exception:
                pass
        return f"[执行失败] {detail}"


def _system_prompt(product: str) -> str:
    """获取对应产品的系统提示词。

    Args:
        product: 产品标识。

    Returns:
        系统提示词文本。
    """
    if product == "sciverse":
        return (
            "你是一个科学数据助手，帮助科研人员使用 Sciverse 平台检索文献。"
            "根据用户的问题，选择合适的函数工具获取数据，然后基于返回结果用中文生成清晰、"
            "有引用依据的回答。回答中应包含文献标题、DOI、年份、关键发现等信息，"
            "帮助用户判断相关性。如果结果为空，如实告知并建议调整检索策略。"
            "如果需要多步检索（如先查字段目录再搜索），请分步调用工具。"
            "工具调用出错时，仔细阅读错误信息修正参数后重试。"
        )
    else:
        return (
            "你是一个化学信息学助手，帮助科研人员使用点石 DianShi 平台检索化学数据。"
            "根据用户的问题，选择合适的函数工具获取数据，然后基于返回结果用中文生成清晰、"
            "结构化的回答。包含化学物质名称、SMILES、分子量、相似度、反应条件等关键信息。"
            "如果结果为空，如实告知并给出建议。"
        )


def generate_chat(product: str, user_message: str):
    """生成 SSE 流式对话响应 — 支持多轮 Agent 工具调用。

    流程：
    1. 发送消息 + 工具定义给 LLM
    2. 如果 LLM 返回工具调用，执行并反馈结果，回到 1（最多 5 轮）
    3. LLM 返回文本回复时，流式输出给前端

    Args:
        product: 产品标识，"sciverse" 或 "dianshi"。
        user_message: 用户输入的自然语言消息。
    """
    tools = SCIVERSE_TOOLS if product == "sciverse" else _wrap_mcp_tools(dianshi_mcp.DIANSHI_TOOLS)

    # 点石前置检查：MCP 服务是否已启用
    if product == "dianshi" and not dianshi_mcp.check_available():
        yield f"data: {json.dumps({'type': 'error', 'message': '点石 MCP 服务未启用，请联系管理员开通权限。'}, ensure_ascii=False)}\n\n"
        return

    messages = [
        {"role": "system", "content": _system_prompt(product)},
        {"role": "user", "content": user_message},
    ]

    text = '正在分析你的问题...\n\n'
    yield f"data: {json.dumps({'type': 'chunk', 'text': text}, ensure_ascii=False)}\n\n"

    max_rounds = 10
    consecutive_errors = 0
    for _round in range(max_rounds):
        try:
            decision = _llm_request(messages, tools)
        except Exception as exc:
            _logger.exception("LLM 调用失败（第 %d 轮）", _round + 1)
            yield f"data: {json.dumps({'type': 'error', 'message': f'LLM 调用失败: {exc}'}, ensure_ascii=False)}\n\n"
            return

        choice = decision.get("choices", [{}])[0]
        msg = choice.get("message", {})
        tool_calls = msg.get("tool_calls", [])

        if tool_calls:
            # 本轮有工具调用 → 执行并继续循环
            messages.append(msg)
            has_error = False
            for tc in tool_calls:
                func_info = tc.get("function", {})
                func_name = func_info.get("name", "")
                try:
                    func_args = json.loads(func_info.get("arguments", "{}"))
                except json.JSONDecodeError:
                    func_args = {}

                text = f'正在调用 {func_name}...\n\n'
                yield f"data: {json.dumps({'type': 'chunk', 'text': text}, ensure_ascii=False)}\n\n"

                tool_result = _execute_tool(product, func_name, func_args)

                # 检测执行失败，连续错误 2 次则终止
                if isinstance(tool_result, str) and tool_result.startswith("[执行失败]"):
                    has_error = True
                    consecutive_errors += 1
                else:
                    consecutive_errors = 0

                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.get("id", ""),
                    "content": tool_result,
                })

            if has_error and consecutive_errors >= 2:
                yield f"data: {json.dumps({'type': 'error', 'message': '接口连续返回错误，请检查查询参数或稍后重试'}, ensure_ascii=False)}\n\n"
                return

            continue

        # 没有工具调用 → 本轮是文本回复，需要流式输出
        content = msg.get("content", "")

        if not content:
            # 空回复：LLM 可能还想继续，但没带 tool_calls 也没 content
            yield f"data: {json.dumps({'type': 'error', 'message': '模型未返回有效结果，请重试'}, ensure_ascii=False)}\n\n"
            return

        # 直接用本轮 content 作为回复，流式输出
        yield f"data: {json.dumps({'type': 'chunk', 'text': content}, ensure_ascii=False)}\n\n"
        yield f"data: {json.dumps({'type': 'done', 'full_text': content}, ensure_ascii=False)}\n\n"
        return

    # 超出最大轮数仍未结束
    yield f"data: {json.dumps({'type': 'error', 'message': '工具调用轮数过多，请简化问题后重试'}, ensure_ascii=False)}\n\n"
