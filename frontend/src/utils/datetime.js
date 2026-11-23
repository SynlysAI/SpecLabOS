/**
 * 将 ISO 时间统一格式化为北京时间。
 *
 * Args:
 *     value: 后端返回的 ISO 8601 时间文本。
 *
 * Returns:
 *     `YYYY-MM-DD HH:mm:ss` 形式的北京时间；无法解析时返回原文本。
 */
export function formatDateTime(value) {
  if (!value) return "--";
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return String(value);
  const beijingTime = new Date(parsed.getTime() + 8 * 60 * 60 * 1000);
  return beijingTime.toISOString().slice(0, 19).replace("T", " ");
}
