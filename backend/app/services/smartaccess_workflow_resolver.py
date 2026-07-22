"""SmartAccess 工作流运行时占位符解析。"""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from datetime import datetime
from typing import Any
from uuid import uuid4


INPUT_PLACEHOLDER = "{input}"
DATE_PLACEHOLDER = "{date}"


def resolve_runtime_placeholders(
    workflow: dict[str, Any],
    runtime_inputs: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """解析工作流中的运行时输入和日期占位符。

    Args:
        workflow: 待下发的工作流定义。
        runtime_inputs: 以步骤 ID 为键的运行时文本输入。

    Returns:
        已补齐运行时输入和唯一日期标识的工作流副本。

    Raises:
        ValueError: 存在未提供输入值的 `{input}` 占位符时抛出。
    """

    resolved_workflow = deepcopy(workflow)
    values = {
        str(step_id): str(value)
        for step_id, value in (runtime_inputs or {}).items()
    }
    missing_step_ids = [
        str(step.get("id") or "<unknown>")
        for step in resolved_workflow.get("steps", [])
        if _requires_runtime_input(step)
        and str(step.get("id") or "") not in values
    ]
    if missing_step_ids:
        raise ValueError("缺少运行时输入: " + ", ".join(missing_step_ids))

    date_value = _unique_date_value()
    for step in resolved_workflow.get("steps", []):
        _resolve_step_placeholders(step, values, date_value)
    return resolved_workflow


def _requires_runtime_input(step: dict[str, Any]) -> bool:
    """判断工作流步骤是否包含需要人工填写的 `{input}` 占位符。"""

    if step.get("action") == "type" and step.get("input_mode") == "free":
        return _contains_input_placeholder(step.get("value"))
    if step.get("action") != "ocr":
        return False
    return _contains_input_placeholder(
        [step.get("expected_text"), step.get("expected_candidates", [])]
    )


def _resolve_step_placeholders(
    step: dict[str, Any],
    runtime_inputs: Mapping[str, str],
    date_value: str,
) -> None:
    """在单个输入或 OCR 步骤中替换运行时占位符。

    Args:
        step: 待替换的工作流步骤。
        runtime_inputs: 以步骤 ID 为键的运行时文本输入。
        date_value: 当前运行的唯一时间标识。
    """

    step_id = str(step.get("id") or "")
    input_value = runtime_inputs.get(step_id, INPUT_PLACEHOLDER)
    if step.get("action") == "type" and step.get("input_mode") == "free":
        step["value"] = _replace_placeholders(
            step.get("value"),
            input_value,
            date_value,
        )
        return
    if step.get("action") != "ocr":
        return
    step["expected_text"] = _replace_placeholders(
        step.get("expected_text"),
        input_value,
        date_value,
    )
    step["expected_candidates"] = _replace_placeholders(
        step.get("expected_candidates", []),
        input_value,
        date_value,
    )


def _contains_input_placeholder(value: Any) -> bool:
    """判断字符串或嵌套列表中是否含有 `{input}` 占位符。"""

    if isinstance(value, str):
        return INPUT_PLACEHOLDER in value
    if isinstance(value, list):
        return any(_contains_input_placeholder(item) for item in value)
    return False


def _replace_placeholders(value: Any, input_value: str, date_value: str) -> Any:
    """递归替换值中的 `{input}` 和 `{date}` 占位符。"""

    if isinstance(value, str):
        return value.replace(INPUT_PLACEHOLDER, input_value).replace(
            DATE_PLACEHOLDER,
            date_value,
        )
    if isinstance(value, list):
        return [
            _replace_placeholders(item, input_value, date_value)
            for item in value
        ]
    return value


def _unique_date_value() -> str:
    """生成与 SmartAccess 保持一致的唯一时间标识。"""

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    return f"{timestamp}_{uuid4().hex[:8]}"
