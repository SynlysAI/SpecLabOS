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
