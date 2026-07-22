import { http } from "./http";

/**
 * 获取外部实验任务批次列表。
 *
 * Args:
 *     filters: 查询筛选条件。
 *
 * Returns:
 *     外部实验任务批次列表。
 */
export async function fetchExternalExperimentDispatches(filters = {}) {
  const response = await http.get("/api/external-experiment-dispatches", {
    params: {
      keyword: filters.keyword || undefined,
    },
  });
  return response.data.items || [];
}

/**
 * 获取外部实验任务批次详情。
 *
 * Args:
 *     dispatchId: 外部实验任务批次标识。
 *
 * Returns:
 *     外部实验任务批次详情。
 */
export async function fetchExternalExperimentDispatchDetail(dispatchId) {
  const response = await http.get(
    `/api/external-experiment-dispatches/${dispatchId}`
  );
  return response.data;
}
