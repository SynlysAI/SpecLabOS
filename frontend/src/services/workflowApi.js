import { http } from "./http";

/**
 * 获取工作流草稿列表。
 *
 * Returns:
 *     工作流列表数据。
 */
export async function fetchWorkflowDrafts() {
  const response = await http.get("/api/workflows");
  return response.data.items;
}

/**
 * 获取设备动作列表。
 *
 * Args:
 *     deviceKey: 设备唯一标识。
 *
 * Returns:
 *     设备动作列表。
 */
export async function fetchDeviceActions(deviceKey) {
  const response = await http.get(`/api/devices/${deviceKey}/actions`);
  return response.data.items || [];
}

/**
 * 获取运行记录列表。
 *
 * Args:
 *     filters: 查询筛选条件。
 *
 * Returns:
 *     运行记录列表。
 */
export async function fetchWorkflowRuns(filters = {}) {
  const response = await http.get("/api/workflow-runs", {
    params: {
      keyword: filters.keyword || undefined,
      status: filters.status && filters.status !== "all" ? filters.status : undefined,
      source: filters.source && filters.source !== "all" ? filters.source : undefined,
    },
  });
  return response.data.items || [];
}

/**
 * 获取运行详情。
 *
 * Args:
 *     runId: 运行编号。
 *
 * Returns:
 *     单条运行详情。
 */
export async function fetchWorkflowRunDetail(runId) {
  const response = await http.get(`/api/workflow-runs/${runId}`);
  return response.data;
}

/**
 * 规范工作流草稿列表。
 *
 * Args:
 *     items: 原始工作流定义列表。
 *
 * Returns:
 *     统一后的工作流草稿列表。
 */
export function normalizeWorkflowDrafts(items) {
  return items.map((item, index) => ({
    workflow_id: item.workflow_id || `workflow-${index}`,
    name: item.name || "未命名工作流",
    status: item.status || "draft",
  }));
}

/**
 * 提交工作流草稿。
 *
 * Args:
 *     payload: 工作流提交载荷。
 *
 * Returns:
 *     后端返回的工作流结果。
 */
export async function createWorkflow(payload) {
  const response = await http.post("/api/workflows", payload);
  return response.data;
}
