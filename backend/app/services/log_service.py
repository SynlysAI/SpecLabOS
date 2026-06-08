"""设备自动化日志聚合服务。"""

from __future__ import annotations

import csv
import io
import logging
import re
import time
from datetime import date, datetime, timedelta
from pathlib import Path

from app.core.config import DeviceLogSettings

logger = logging.getLogger(__name__)

# ---------- 模块级 TTL 缓存 ----------

_CACHE_TTL = 30
_cache_store: dict[str, tuple[float, object]] = {}

_MISS = object()


def _get_cached(key: str, ttl: int = _CACHE_TTL):
    """从模块级缓存获取值，过期或不存在时返回 _MISS 哨兵。"""
    entry = _cache_store.get(key)
    if entry:
        expiry, value = entry
        if time.time() < expiry:
            return value
        del _cache_store[key]
    return _MISS


def _set_cache(key: str, value: object) -> None:
    """写入模块级 TTL 缓存。"""
    _cache_store[key] = (time.time() + _CACHE_TTL, value)


# ----------------------------------


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

AUTOMATION_METRIC_LABELS = {
    "gpc": "GPC",
    "lcms": "LCMS",
    "nmr": "NMR",
    "raman": "Raman",
}

AUTOMATION_CSV_PATHS = {
    "gpc": "gpc_rate_csv",
    "lcms": "lcms_rate_csv",
    "nmr": "nmr_rate_csv",
}

RAMAN_STEP_DICT = {
    "/raman/jy/camera": "上样对焦",
    "开始粗搜索自动对焦": "初步聚焦",
    "开始精搜索自动对焦": "精确聚焦",
    "/raman/jy/capture": "开始采集",
    "slider pos": "切换激发波长",
    "采集流程完成": "采集完成",
}

RAMAN_STEP_KEYS = list(RAMAN_STEP_DICT.keys())
RAMAN_START_KEY = "/raman/jy/camera"
RAMAN_END_KEY = "采集流程完成"


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
        selected_date: str | None = None,
        limit: int = 300,
    ) -> list[dict]:
        """返回统一标准化后的设备日志列表。

        Args:
            keyword: 日志关键字过滤条件。
            level: 日志级别过滤条件。
            source: 日志来源过滤条件。
            selected_date: 指定查询日期，格式为 YYYY-MM-DD。
            limit: 返回结果数量上限。

        Returns:
            已按时间倒序排列的日志列表。
        """
        cache_key = f"list_logs:{selected_date}:{keyword}:{level}:{source}"
        cached = _get_cached(cache_key)
        if cached is not _MISS:
            return cached

        normalized_keyword = self._normalize_filter_value(keyword)
        normalized_level = self._normalize_filter_value(level)
        normalized_source = self._normalize_filter_value(source)
        target_date = self._parse_selected_date(selected_date)

        items = (
            self._collect_raman_logs(target_date)
            + self._collect_gpc_lcms_logs(target_date)
            + self._collect_nmr_logs(target_date)
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
        result = [self._strip_internal_fields(item) for item in filtered_items[:limit]]
        _set_cache(cache_key, result)
        return result

    def get_automation_rate_summary(self) -> dict:
        """汇总设备自动化率摘要。

        Returns:
            包含总自动化率与各设备明细的摘要字典。
        """
        cache_key = "automation_rate_summary"
        cached = _get_cached(cache_key)
        if cached is not _MISS:
            return cached

        metrics = [
            self._collect_csv_automation_metric("gpc"),
            self._collect_csv_automation_metric("lcms"),
            self._collect_csv_automation_metric("nmr"),
            self._collect_raman_automation_metric(),
        ]
        valid_rates = [metric["rate"] for metric in metrics if metric["sample_count"] > 0]
        overall_rate = round(sum(valid_rates) / len(valid_rates), 4) if valid_rates else 0.0
        result = {
            "overall_rate": overall_rate,
            "metrics": metrics,
        }
        _set_cache(cache_key, result)
        return result

    def _collect_raman_logs(self, target_date: date) -> list[dict]:
        """收集 Raman 指定日期日志中的有效实验记录。

        Args:
            target_date: 目标查询日期。

        Returns:
            Raman 标准化日志列表。
        """
        try:
            target_file = Path(self._settings.raman_dir) / (
                f"ExRaman_{target_date.strftime('%Y-%m-%d')}.log"
            )
            if not target_file.is_file():
                return []
        except OSError as exc:
            logger.warning("Raman 日志目录不可访问，已跳过: %s", exc)
            return []

        items: list[dict] = []
        last_created_at = ""
        for index, line in enumerate(self._read_lines(target_file)):
            if not self._is_raman_signal(line):
                continue
            parsed_line = self._parse_raman_line(
                line=line.strip(),
                fallback_created_at=last_created_at,
            )
            if not parsed_line:
                continue
            created_at = parsed_line["created_at"]
            message = parsed_line["message"]
            if created_at:
                last_created_at = created_at
            items.append(
                self._build_log_item(
                    log_id=f"raman-{index}",
                    level="info",
                    source="raman",
                    service_name=self._infer_raman_service_name(message),
                    message=message,
                    created_at=created_at,
                    file_path=str(target_file),
                    raw_content=line.strip(),
                )
            )
        return items

    def _collect_gpc_lcms_logs(self, target_date: date) -> list[dict]:
        """收集 GPC/LCMS 指定日期前处理 info 日志。

        Args:
            target_date: 目标查询日期。

        Returns:
            GPC/LCMS 标准化日志列表。
        """
        try:
            target_file = Path(self._settings.gpc_lcms_dir) / (
                f"info-{target_date.strftime('%Y-%m-%d')}.log"
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

    def _collect_nmr_logs(self, target_date: date) -> list[dict]:
        """收集 NMR 指定日期 TaskFlow 实验操作日志。

        Args:
            target_date: 目标查询日期。

        Returns:
            NMR 标准化日志列表。
        """
        try:
            target_dir = Path(self._settings.nmr_dir) / target_date.strftime("%Y-%m-%d") / "TaskFlow"
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

    def _collect_csv_automation_metric(self, metric_key: str) -> dict:
        """读取 CSV 文件并计算设备自动化率。

        Args:
            metric_key: 指标编码，支持 gpc、lcms、nmr。

        Returns:
            单个设备的自动化率指标字典。
        """
        csv_path = getattr(self._settings, AUTOMATION_CSV_PATHS[metric_key], "")
        rows = self._read_csv_rows(csv_path)
        rate_values: list[float] = []

        for row in rows:
            normalized_device = str(row.get("device_select", "")).strip().lower()
            if metric_key in {"gpc", "lcms"} and normalized_device != metric_key:
                continue
            rate_value = self._parse_float(row.get("final_auto_rate"))
            if rate_value is None:
                continue
            rate_values.append(rate_value)

        description = (
            f"读取统计表 {csv_path} 的 final_auto_rate 字段。"
            if csv_path
            else "未配置统计表路径。"
        )
        if csv_path and not rows:
            description = f"未从 {csv_path} 读取到有效数据。"

        average_rate = round(sum(rate_values) / len(rate_values), 4) if rate_values else 0.0
        completed_count = len([item for item in rate_values if item >= 1])
        return self._build_automation_metric(
            key=metric_key,
            rate=average_rate,
            sample_count=len(rate_values),
            completed_count=completed_count,
            source_type="csv",
            description=description,
        )

    def _collect_raman_automation_metric(self) -> dict:
        """根据最近 10 次 Raman 实验统计自动化率。

        Returns:
            Raman 自动化率指标字典。
        """
        recent_limit = 10
        experiments = self._collect_recent_raman_experiments(recent_limit)
        experiment_rates = [self._calculate_raman_experiment_rate(experiment) for experiment in experiments]
        average_rate = (
            round(sum(experiment_rates) / len(experiment_rates), 4)
            if experiment_rates
            else 0.0
        )
        completed_count = len([item for item in experiment_rates if item >= 1])
        description = (
            f"基于最近 {recent_limit} 次 Raman 实验自动步骤完成情况统计。"
            if experiments
            else f"未识别到最近 {recent_limit} 次 Raman 实验片段。"
        )
        return self._build_automation_metric(
            key="raman",
            rate=average_rate,
            sample_count=len(experiment_rates),
            completed_count=completed_count,
            source_type="log",
            description=description,
        )

    def _collect_recent_raman_experiments(self, recent_limit: int) -> list[list[str]]:
        """提取最近若干次 Raman 实验步骤。

        Args:
            recent_limit: 需要返回的最近实验次数。

        Returns:
            按时间升序排列的最近实验步骤列表。
        """
        if recent_limit <= 0:
            return []

        try:
            raman_dir = Path(self._settings.raman_dir)
            if not raman_dir.is_dir():
                return []
        except OSError:
            return []

        log_files = sorted(
            raman_dir.glob("ExRaman_*.log"),
            key=lambda path: path.name,
            reverse=True,
        )
        if not log_files:
            return []

        collected_logs: list[dict] = []
        collected_experiments: list[list[str]] = []

        for log_file in log_files:
            target_date = self._extract_raman_date_from_filename(log_file.name)
            if not target_date:
                continue
            collected_logs.extend(self._collect_raman_logs(target_date))
            collected_experiments = self._split_raman_experiments(collected_logs)
            if len(collected_experiments) >= recent_limit:
                break

        if not collected_experiments:
            return []
        return collected_experiments[-recent_limit:]

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
    def _read_csv_rows(csv_path: str) -> list[dict[str, str]]:
        """读取 CSV 行数据。

        Args:
            csv_path: CSV 文件路径。

        Returns:
            CSV 字典行列表。
        """
        if not csv_path:
            return []
        file_path = Path(csv_path)
        if not file_path.is_file():
            return []
        try:
            raw_bytes = file_path.read_bytes()
        except OSError:
            return []

        candidate_encodings = [
            "utf-8-sig",
            "utf-8",
            "gb18030",
            "gbk",
            "cp936",
            "big5",
            "latin1",
        ]

        for encoding in candidate_encodings:
            try:
                decoded_text = raw_bytes.decode(encoding)
                reader = csv.DictReader(io.StringIO(decoded_text))
                return list(reader)
            except UnicodeDecodeError:
                continue
            except csv.Error:
                continue

        try:
            decoded_text = raw_bytes.decode("utf-8-sig", errors="ignore")
            reader = csv.DictReader(io.StringIO(decoded_text))
            logger.warning("CSV 编码异常，已使用忽略非法字节模式读取: %s", file_path)
            return list(reader)
        except csv.Error:
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
    def _infer_raman_service_name(message: str) -> str:
        """根据日志内容推断 Raman 日志模块名称。

        Args:
            message: Raman 日志正文。

        Returns:
            面向页面展示的服务模块名称。
        """
        if message.startswith("body:"):
            return "优化参数"

        if "/raman/jy/camera" in message:
            return "进样对焦"

        if "开始粗搜索自动对焦" in message:
            return "初步聚焦"

        if "开始精搜索自动对焦" in message:
            return "精确对焦"

        if "slider pos" in message:
            return "自动选择激发波长"

        if "/raman/jy/capture" in message:
            return "开始采集"

        if "采集流程完成" in message:
            return "采集完成"

        acquisition_keywords = [
            "Starting acquisition",
            "Actual exposure time",
            "Actual accumulation",
            "Actual kinetic",
            "laser pulse",
            "laser:",
        ]
        if any(keyword in message for keyword in acquisition_keywords):
            return "光谱采集"

        callback_keywords = [
            "JY req:",
            "body:",
            "JY status callback",
            "JY capture req accepted",
            "JY http response sent",
            "JY callback",
            "sltJyHttpReqCapture",
            "sltJyHttpCallback",
        ]
        if any(keyword in message for keyword in callback_keywords):
            return "接口通信"

        return "光谱采集"

    @staticmethod
    def _parse_raman_line(line: str, fallback_created_at: str) -> dict | None:
        """解析 Raman 单行日志或关联参数行。

        Args:
            line: 单行日志文本。
            fallback_created_at: 无时间戳行继承的上一条时间。

        Returns:
            解析后的字段字典，无法解析时返回 None。
        """
        matched = RAMAN_LINE_PATTERN.match(line)
        if matched:
            return {
                "created_at": matched.group("created_at"),
                "message": matched.group("message").strip().strip('"'),
            }

        if line.startswith("body:") and fallback_created_at:
            return {
                "created_at": fallback_created_at,
                "message": line.strip(),
            }

        return None

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
    def _build_automation_metric(
        key: str,
        rate: float,
        sample_count: int,
        completed_count: int,
        source_type: str,
        description: str,
    ) -> dict:
        """构造单个自动化率指标。

        Args:
            key: 指标编码。
            rate: 自动化率数值。
            sample_count: 样本总数。
            completed_count: 完整完成样本数。
            source_type: 数据来源类型。
            description: 指标说明。

        Returns:
            自动化率指标字典。
        """
        return {
            "key": key,
            "label": AUTOMATION_METRIC_LABELS[key],
            "rate": round(rate, 4),
            "sample_count": sample_count,
            "completed_count": completed_count,
            "source_type": source_type,
            "description": description,
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
    def _parse_selected_date(value: str | None) -> date:
        """解析查询日期参数。

        Args:
            value: 前端传入的日期字符串，格式为 YYYY-MM-DD。

        Returns:
            解析成功后的日期对象，失败时返回当天日期。
        """
        if isinstance(value, str):
            try:
                return datetime.strptime(value.strip(), "%Y-%m-%d").date()
            except ValueError:
                pass
        return datetime.now().date()

    @staticmethod
    def _extract_raman_date_from_filename(filename: str) -> date | None:
        """从 Raman 日志文件名提取日期。

        Args:
            filename: Raman 日志文件名。

        Returns:
            提取成功的日期对象，失败时返回 None。
        """
        matched = re.search(r"ExRaman_(\d{4}-\d{2}-\d{2})\.log$", filename)
        if not matched:
            return None
        try:
            return datetime.strptime(matched.group(1), "%Y-%m-%d").date()
        except ValueError:
            return None

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

    @staticmethod
    def _parse_float(value: object) -> float | None:
        """将任意值解析为浮点数。

        Args:
            value: 原始值。

        Returns:
            浮点数，失败时返回 None。
        """
        if value in {"", None}:
            return None
        try:
            return float(str(value).strip())
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _extract_raman_step_key(message: str) -> str | None:
        """从 Raman 日志正文中识别自动化步骤键。

        Args:
            message: 日志正文。

        Returns:
            匹配到的步骤键，未命中时返回 None。
        """
        for step_key in RAMAN_STEP_KEYS:
            if step_key in message:
                return step_key
        return None

    def _split_raman_experiments(self, log_records: list[dict]) -> list[list[str]]:
        """按开始和结束标识切分 Raman 实验步骤。

        Args:
            log_records: Raman 日志记录列表。

        Returns:
            每次实验对应的步骤键列表。
        """
        ordered_records = sorted(
            log_records,
            key=lambda item: item.get("_sort_at", datetime.min),
        )
        experiments: list[list[str]] = []
        current_steps: list[str] = []

        for record in ordered_records:
            step_key = self._extract_raman_step_key(str(record.get("message", "")))
            if not step_key:
                continue
            if step_key == RAMAN_START_KEY:
                if current_steps:
                    experiments.append(current_steps)
                current_steps = [step_key]
                continue
            if not current_steps:
                continue
            if step_key not in current_steps:
                current_steps.append(step_key)
            if step_key == RAMAN_END_KEY:
                experiments.append(current_steps)
                current_steps = []

        if current_steps:
            experiments.append(current_steps)
        return experiments

    @staticmethod
    def _calculate_raman_experiment_rate(step_keys: list[str]) -> float:
        """计算单次 Raman 实验的自动化率。

        Args:
            step_keys: 单次实验识别到的步骤键列表。

        Returns:
            当前实验的自动化率。
        """
        if not step_keys or step_keys[0] != RAMAN_START_KEY:
            return 0.0
        matched_steps = len({key for key in step_keys if key in RAMAN_STEP_DICT})
        return round(matched_steps / len(RAMAN_STEP_DICT), 4)
