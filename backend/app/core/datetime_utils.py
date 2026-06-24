"""时间格式化工具。"""

from datetime import datetime, timedelta, timezone

CHINA_TZ = timezone(timedelta(hours=8))


def format_datetime(value) -> str:
    """格式化运行时间字段为中国时区 (UTC+8) 字符串。

    Args:
        value: 原始时间值（datetime 对象或 ISO 字符串）。

    Returns:
        格式化后的北京时间字符串。
    """
    if value is None:
        return "--"

    if hasattr(value, "strftime"):
        if value.tzinfo is not None and value.tzinfo.utcoffset(value) is not None:
            value = value.astimezone(CHINA_TZ)
        else:
            # MongoDB 读取后时区信息丢失，但存储时统一为 UTC
            value = value.replace(tzinfo=timezone.utc).astimezone(CHINA_TZ)
        return value.strftime("%Y-%m-%d %H:%M")

    raw_str = str(value)
    if "T" in raw_str or "+" in raw_str or raw_str.endswith("Z"):
        try:
            parsed = datetime.fromisoformat(raw_str)
            if parsed.tzinfo is not None:
                parsed = parsed.astimezone(CHINA_TZ)
            else:
                parsed = parsed.replace(tzinfo=timezone.utc).astimezone(CHINA_TZ)
            return parsed.strftime("%Y-%m-%d %H:%M")
        except (ValueError, TypeError):
            pass
    return raw_str
