import { http } from "./http";

/**
 * 获取 SmartAccess 模板列表。
 *
 * Args:
 *     filters: 查询筛选条件。
 *
 * Returns:
 *     模板列表。
 */
export async function fetchSmartAccessTemplates(filters = {}) {
  const response = await http.get("/api/smartaccess/templates", {
    params: {
      keyword: filters.keyword || undefined,
      device_id: filters.device_id || undefined,
      status: filters.status && filters.status !== "all" ? filters.status : undefined,
    },
  });
  return response.data.items || [];
}

/**
 * 获取 SmartAccess 模板详情。
 *
 * Args:
 *     templateId: 模板 ID。
 *     templateVersion: 模板版本。
 *
 * Returns:
 *     模板详情。
 */
export async function fetchSmartAccessTemplateDetail(templateId, templateVersion) {
  const response = await http.get(
    `/api/smartaccess/templates/${templateId}/versions/${templateVersion}`
  );
  return response.data;
}

/**
 * 发起 SmartAccess 远程运行。
 *
 * Args:
 *     payload: 运行创建请求。
 *
 * Returns:
 *     运行创建结果。
 */
export async function createSmartAccessRun(payload) {
  const response = await http.post("/api/smartaccess/runs", payload);
  return response.data;
}

/**
 * 获取 SmartAccess 运行记录列表。
 *
 * Args:
 *     filters: 查询筛选条件。
 *
 * Returns:
 *     运行记录列表。
 */
export async function fetchSmartAccessRuns(filters = {}) {
  const response = await http.get("/api/smartaccess/runs", {
    params: {
      keyword: filters.keyword || undefined,
      status: filters.status && filters.status !== "all" ? filters.status : undefined,
    },
  });
  return response.data.items || [];
}

/**
 * 获取 SmartAccess 运行详情。
 *
 * Args:
 *     runId: 运行编号。
 *
 * Returns:
 *     单条运行详情。
 */
export async function fetchSmartAccessRunDetail(runId) {
  const response = await http.get(`/api/smartaccess/runs/${runId}`);
  return response.data;
}
