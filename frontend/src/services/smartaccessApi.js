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
