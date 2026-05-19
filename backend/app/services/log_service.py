"""设备自动化日志聚合服务。"""

from __future__ import annotations

import logging
import re
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

from app.core.config import DeviceLogSettings


RAMAN_SIGNAL_PATTERNS = [
    "JY req:",
    "body:",
    "JY status callback",
    "JY capture req accepted",
    "JY http response sent",
    "JY callback",
    "sltJyHttpReqCapture",
    "sltJyHttpCallback",
    "JY 采集流程完成",
    "Actual exposure time",
    "Actual accumulation",
    "Actual kinetic",
    "Starting acquisition",
    "laser pulse",
    "laser:",
    "slider pos",
    "对焦",
    "Brightness",
    "select set max rate",
]

RAMAN_LINE_PATTERN = re.compile(
    r"^thread_id<(?P<thread_id>[^>]+)>:(?P<created_at>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})"
    r"\[:(?P<code>-?\d+)\]:(?P<message>.*)$"
)
NMR_LINE_PATTERN = re.compile(
    r"^\s*\[(?P<created_at>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d+)\] "
    r"\[(?P<level>[A-Z]+)\]: (?P<message>.*)$"
)

SOURCE_LABEL_MAP = {
    "raman": "Raman",
    "gpc-lcms": "GPC/LCMS",
    "nmr": "NMR",
}


class DeviceLogService:
    """聚合 Raman、GPC/LCMS、NMR 的设备自动化日志。"""

    def __init__(self, settings: DeviceLogSettings) -> None:
        """初始化日志聚合服务。

        Args:
            settings: 设备日志目录配置。
        """
        self._settings = settings

    def list_logs(
        self,
        keyword: str | None = None,
        level: str | None = None,
        source: str | None = None,
        limit: int = 300,
    ) -> list[dict]:
        """返回统一标准化后的设备日志列表。

        Args:
            keyword: 日志关键字过滤条件。
            level: 日志级别过滤条件。
            source: 日志来源过滤条件。
            limit: 返回结果数量上限。

        Returns:
            已按时间倒序排列的日志列表。
        """
        normalized_keyword = self._normalize_filter_value(keyword)
        normalized_level = self._normalize_filter_value(level)
        normalized_source = self._normalize_filter_value(source)

        items = (
            self._collect_raman_logs()
            + self._collect_gpc_lcms_logs()
            + self._collect_nmr_logs()
        )

        filtered_items = [
            item
            for item in items
            if self._match_keyword(item, normalized_keyword)
            and self._match_level(item, normalized_level)
            and self._match_source(item, normalized_source)
        ]
        filtered_items.sort(
            key=lambda item: item.get("_sort_at", datetime.min),
            reverse=True,
        )
        return [self._strip_internal_fields(item) for item in filtered_items[:limit]]

    def _collect_raman_logs(self) -> list[dict]:
        """收集 Raman 当日日志中的有效实验记录。

        Returns:
            Raman 标准化日志列表。
        """
        try:
            target_file = Path(self._settings.raman_dir) / (
                f"ExRaman_{datetime.now().strftime('%Y-%m-%d')}.log"
            )
            if not target_file.is_file():
                return []
        except OSError as exc:
            logger.warning("Raman 日志目录不可访问，已跳过: %s", exc)
            return []

        items: list[dict] = []
        for index, line in enumerate(self._read_lines(target_file)):
            if not self._is_raman_signal(line):
                continue
            matched = RAMAN_LINE_PATTERN.match(line.strip())
            if not matched:
                continue
            created_at = matched.group("created_at")
            message = matched.group("message").strip().strip('"')
            items.append(
                self._build_log_item(
                    log_id=f"raman-{index}",
                    level="info",
                    source="raman",
                    service_name="光谱采集",
                    message=message,
                    created_at=created_at,
                    file_path=str(target_file),
                    raw_content=line.strip(),
                )
            )
        return items

    def _collect_gpc_lcms_logs(self) -> list[dict]:
        """收集 GPC/LCMS 前处理 info 日志。

        Returns:
            GPC/LCMS 标准化日志列表。
        """
        try:
            target_file = Path(self._settings.gpc_lcms_dir) / (
                f"info-{datetime.now().strftime('%Y-%m-%d')}.log"
            )
            if not target_file.is_file():
                return []
        except OSError as exc:
            logger.warning("GPC/LCMS 日志目录不可访问，已跳过: %s", exc)
            return []

        items: list[dict] = []
        for index, line in enumerate(self._read_lines(target_file)):
            parsed_line = self._parse_gpc_lcms_line(line.strip())
            if not parsed_line:
                continue
            created_at = parsed_line["created_at"]
            raw_level = parsed_line["level"]
            message = parsed_line["message"]
            logger_name = parsed_line["logger"]
            items.append(
                self._build_log_item(
                    log_id=f"gpc-lcms-{index}",
                    level=self._normalize_level(raw_level),
                    source="gpc-lcms",
                    service_name=self._infer_gpc_lcms_service_name(message, logger_name),
                    message=message,
                    created_at=created_at,
                    file_path=str(target_file),
                    raw_content=line.strip(),
                )
            )
        return items

    def _collect_nmr_logs(self) -> list[dict]:
        """收集 NMR TaskFlow 实验操作日志。

        Returns:
            NMR 标准化日志列表。
        """
        try:
            current_date = datetime.now().strftime("%Y-%m-%d")
            target_dir = Path(self._settings.nmr_dir) / current_date / "TaskFlow"
            if not target_dir.is_dir():
                return []
        except OSError as exc:
            logger.warning("NMR 日志目录不可访问，已跳过: %s", exc)
            return []

        items: list[dict] = []
        for file_path in sorted(target_dir.glob("*.log")):
            for index, line in enumerate(self._read_lines(file_path)):
                matched = NMR_LINE_PATTERN.match(line.strip())
                if not matched:
                    continue
                created_at = matched.group("created_at")
                raw_level = matched.group("level")
                message = matched.group("message").strip()
                items.append(
                    self._build_log_item(
                        log_id=f"nmr-{file_path.stem}-{index}",
                        level=self._normalize_level(raw_level),
                        source="nmr",
                        service_name="TaskFlow",
                        message=message,
                        created_at=created_at,
                        file_path=str(file_path),
                        raw_content=line.strip(),
                    )
                )
        return items

    @staticmethod
    def _read_lines(file_path: Path) -> list[str]:
        """按 UTF-8 容错读取日志文件内容。

        Args:
            file_path: 目标日志文件路径。

        Returns:
            日志文本行列表。
        """
        try:
            return file_path.read_text(encoding="utf-8", errors="ignore").splitlines()
        except OSError:
            return []

    @staticmethod
    def _is_raman_signal(line: str) -> bool:
        """判断 Raman 日志行是否为实验相关有效日志。

        Args:
            line: 单行日志文本。

        Returns:
            是否命中 Raman 有效日志白名单。
        """
        return any(pattern in line for pattern in RAMAN_SIGNAL_PATTERNS)

    @staticmethod
    def _normalize_level(raw_level: str) -> str:
        """将原始日志级别统一映射为前端可展示的状态值。

        Args:
            raw_level: 原始日志级别文本。

        Returns:
            统一后的日志级别。
        """
        level = raw_level.lower()
        if level in {"info", "debug"}:
            return "info"
        if level in {"warning", "warn"}:
            return "warning"
        if level in {"error", "critical"}:
            return "error"
        return "idle"

    @staticmethod
    def _infer_gpc_lcms_service_name(message: str, logger_name: str) -> str:
        """根据日志内容推断 GPC/LCMS 日志模块名称。

        Args:
            message: 日志正文。
            logger_name: 原始 logger 文件名。

        Returns:
            面向页面展示的服务模块名称。
        """
        upper_message = message.upper()
        if "LCMS" in upper_message:
            return "LCMS 前处理"
        if "GPC" in upper_message:
            return "GPC 前处理"
        if "PLC" in upper_message:
            return "PLC 控制"
        return logger_name.replace(".py", "")

    @staticmethod
    def _match_keyword(item: dict, keyword: str) -> bool:
        """判断日志项是否命中关键字过滤条件。

        Args:
            item: 标准化日志项。
            keyword: 关键字过滤条件。

        Returns:
            是否匹配。
        """
        if not keyword:
            return True
        haystack = " ".join(
            [
                str(item.get("message", "")),
                str(item.get("service_name", "")),
                str(item.get("source", "")),
                str(item.get("source_label", "")),
            ]
        ).lower()
        return keyword in haystack

    @staticmethod
    def _match_level(item: dict, level: str) -> bool:
        """判断日志项是否命中级别过滤条件。

        Args:
            item: 标准化日志项。
            level: 级别过滤条件。

        Returns:
            是否匹配。
        """
        return not level or item.get("level") == level

    @staticmethod
    def _match_source(item: dict, source: str) -> bool:
        """判断日志项是否命中来源过滤条件。

        Args:
            item: 标准化日志项。
            source: 来源过滤条件。

        Returns:
            是否匹配。
        """
        return not source or item.get("source") == source

    @staticmethod
    def _build_log_item(
        log_id: str,
        level: str,
        source: str,
        service_name: str,
        message: str,
        created_at: str,
        file_path: str,
        raw_content: str,
    ) -> dict:
        """构造统一格式的日志项。

        Args:
            log_id: 日志唯一标识。
            level: 日志级别。
            source: 日志来源编码。
            service_name: 展示用服务模块名称。
            message: 展示用日志正文。
            created_at: 日志时间文本。
            file_path: 日志文件路径。
            raw_content: 原始日志内容。

        Returns:
            可直接返回给接口层的日志字典。
        """
        return {
            "id": log_id,
            "level": level,
            "source": source,
            "source_label": SOURCE_LABEL_MAP.get(source, source),
            "service_name": service_name,
            "message": message,
            "created_at": created_at,
            "file_path": file_path,
            "raw_content": raw_content,
            "_sort_at": DeviceLogService._parse_datetime(created_at),
        }

    @staticmethod
    def _parse_datetime(value: str) -> datetime:
        """解析日志时间文本。

        Args:
            value: 日志时间字符串。

        Returns:
            解析后的时间对象，失败时返回最小时间。
        """
        formats = [
            "%Y-%m-%d %H:%M:%S.%f",
            "%Y-%m-%d %H:%M:%S",
        ]
        for item_format in formats:
            try:
                return datetime.strptime(value, item_format)
            except ValueError:
                continue
        return datetime.min

    @staticmethod
    def _strip_internal_fields(item: dict) -> dict:
        """移除接口响应中不需要的内部排序字段。

        Args:
            item: 标准化日志项。

        Returns:
            清理后的日志项。
        """
        normalized_item = dict(item)
        normalized_item.pop("_sort_at", None)
        return normalized_item

    @staticmethod
    def _normalize_filter_value(value: str | None) -> str:
        """标准化接口过滤条件。

        Args:
            value: 原始过滤参数值。

        Returns:
            去除空白并转小写后的过滤值，无法处理时返回空字符串。
        """
        if not isinstance(value, str):
            return ""
        return value.strip().lower()

    @staticmethod
    def _parse_gpc_lcms_line(line: str) -> dict | None:
        """解析 GPC/LCMS 单行日志。

        Args:
            line: 单行日志文本。

        Returns:
            解析后的字段字典，无法解析时返回 None。
        """
        parts = line.split(" - ", 6)
        if len(parts) < 7:
            return None
        created_at, level, logger_name, function_name, thread_name, line_no, message = parts
        if not re.match(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$", created_at):
            return None
        if not line_no.isdigit():
            return None
        return {
            "created_at": created_at,
            "level": level.strip(),
            "logger": logger_name.strip(),
            "function": function_name.strip(),
            "thread": thread_name.strip(),
            "line_no": line_no.strip(),
            "message": message.strip(),
        }
