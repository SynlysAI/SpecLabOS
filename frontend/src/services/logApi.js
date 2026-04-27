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
      level: filters.level && filters.level !== "all" ? filters.level : undefined
    }
  });
  return response.data.items || [];
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
