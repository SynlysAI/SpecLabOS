"""时间格式化工具。"""


def format_datetime(value) -> str:
    """格式化运行时间字段。

    Args:
        value: 原始时间值。

    Returns:
        格式化后的时间字符串。
    """
    if value is None:
        return "--"
    if hasattr(value, "strftime"):
        return value.strftime("%Y-%m-%d %H:%M")
    return str(value)
