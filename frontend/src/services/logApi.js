import { http } from "./http";

/**
 * 获取系统日志列表。
 *
 * Args:
 *     filters: 日志筛选条件。
 *
 * Returns:
 *     日志列表数据。
 */
export async function fetchSystemLogs(filters = {}) {
  const response = await http.get("/api/logs", {
    params: {
      keyword: filters.keyword || undefined,
      level: filters.level && filters.level !== "all" ? filters.level : undefined,
      source: filters.source && filters.source !== "all" ? filters.source : undefined,
      date: filters.date || undefined
    }
  });
  return response.data.items || [];
}

/**
 * 获取设备自动化率摘要。
 *
 * Returns:
 *     自动化率摘要数据。
 */
export async function fetchAutomationRateSummary() {
  const response = await http.get("/api/logs/automation-rate");
  return response.data || { overall_rate: 0, metrics: [] };
}

/**
 * 获取单条日志详情。
 *
 * Args:
 *     logId: 日志唯一标识。
 *
 * Returns:
 *     单条日志详情。
 */
export async function fetchLogDetail(logId) {
  const response = await http.get(`/api/logs/${logId}`);
  return response.data;
}
