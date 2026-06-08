"""工具服务路由。"""

import json
import logging
from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from langchain_openai import ChatOpenAI
from pydantic import BaseModel

from app.core.config import get_settings

router = APIRouter(prefix="/api/tools", tags=["tools"])
_logger = logging.getLogger(__name__)

_REF_DIR = Path(__file__).resolve().parent / "data"


class ParseInstructionsRequest(BaseModel):
    """指令解析请求参数。

    Args:
        experiment_plan: 用户输入的实验方案文本。
    """
    experiment_plan: str


def _read_reference_file(filename: str, max_chars: int = 8000) -> str:
    """读取参考文件内容。

    Args:
        filename: 文件名。
        max_chars: 最大读取字符数。

    Returns:
        文件文本内容。
    """
    file_path = _REF_DIR / filename
    if not file_path.exists():
        _logger.warning("参考文件不存在: %s", file_path)
        return ""
    try:
        return file_path.read_text(encoding="utf-8")[:max_chars]
    except UnicodeDecodeError:
        return file_path.read_text(encoding="gbk")[:max_chars]


def _build_llm_client() -> ChatOpenAI:
    """基于全局配置创建 LLM 客户端实例。

    Returns:
        langchain ChatOpenAI 流式客户端。
    """
    llm_config = get_settings().llm
    return ChatOpenAI(
        model=llm_config.model,
        api_key=llm_config.api_key,
        base_url=llm_config.base_url,
        streaming=True,
        temperature=0,
        max_tokens=4096,
    )


@router.post("/parse-instructions")
def parse_instructions(payload: ParseInstructionsRequest) -> StreamingResponse:
    """流式解析实验方案，生成设备控制指令并返回格式化指令列表。

    Args:
        payload: 包含实验方案的请求体。

    Returns:
        SSE 流式响应，包含 type=chunk（流式文本）和 type=done（最终指令列表）。
    """

    def _generate():
        try:
            llm = _build_llm_client()
        except Exception as exc:
            _logger.exception("创建 LLM 客户端失败")
            yield f"data: {json.dumps({'type': 'error', 'message': f'LLM 客户端初始化失败: {exc}'}, ensure_ascii=False)}\n\n"
            return

        standard_flow = _read_reference_file("标准控制指令流程_new.txt")
        optimization_params = _read_reference_file("优化参数输入.txt")

        messages = [
            (
                "system",
                "你是一个了解化学流程和编程语言的助手，需要你根据给定的优化参数，"
                "生成符合指令集定义的设备控制指令。",
            ),
            (
                "user",
                f"请参考以下文件内容回答问题：\n\n"
                f"{standard_flow}\n\n"
                f"{optimization_params}\n\n"
                f"请你先学习优化参数输入文档和这份标准控制指令流程之间的对应关系，"
                f"标准控制流程是依照优化参数输入而生成的。"
                f"然后根据你学习到的对应关系，给出以下优化参数输入的标准控制流程指令：\n"
                f"优化参数如下：\n{payload.experiment_plan}",
            ),
        ]

        full_content = ""
        try:
            for chunk in llm.stream(messages):
                if chunk.content:
                    full_content += chunk.content
                    yield f"data: {json.dumps({'type': 'chunk', 'text': chunk.content}, ensure_ascii=False)}\n\n"
        except Exception as exc:
            _logger.exception("LLM 流式调用失败")
            yield f"data: {json.dumps({'type': 'error', 'message': f'LLM 调用失败: {exc}'}, ensure_ascii=False)}\n\n"
            return

        instructions = [
            line.strip()
            for line in full_content.splitlines()
            if line.strip().startswith("S ")
        ]
        yield f"data: {json.dumps({'type': 'done', 'instructions': instructions, 'full_text': full_content}, ensure_ascii=False)}\n\n"

    return StreamingResponse(_generate(), media_type="text/event-stream")
