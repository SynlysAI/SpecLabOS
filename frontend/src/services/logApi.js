import { http } from "./http";

/** 日志接口涉及对象存储读取，超时设置较长。 */
const LOG_API_TIMEOUT = 60000;

/**
 * 获取数据中心日志文件列表。
 *
 * Args:
 *     filters: 日志筛选条件。
 *
 * Returns:
 *     日志文件列表和匹配总数。
 */
export async function fetchSystemLogs(filters = {}) {
  const response = await http.get("/api/logs", {
    params: {
      keyword: filters.keyword || undefined,
      device_id: filters.device_id || undefined,
      date: filters.date || undefined,
      days: filters.days ?? 7,
      limit: filters.limit || 100
    },
    timeout: LOG_API_TIMEOUT
  });
  return {
    items: response.data?.items || [],
    total: response.data?.total || 0
  };
}

/**
 * 获取日志文件文本内容。
 *
 * Args:
 *     fileId: 日志文件 ID。
 *
 * Returns:
 *     日志文件内容和截断标记。
 */
export async function fetchLogContent(fileId) {
  const response = await http.get(`/api/logs/${fileId}/content`, {
    timeout: LOG_API_TIMEOUT
  });
  return response.data || { content: "", truncated: false };
}
