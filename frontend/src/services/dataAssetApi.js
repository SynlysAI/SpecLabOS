import { http } from "./http";

/**
 * 获取 SmartDataHub 数据资产概览。
 *
 * Returns:
 *     数据资产全量统计与分布信息。
 */
export async function fetchDataAssetOverview() {
  const response = await http.get("/api/data/overview");
  return response.data || {};
}

/**
 * 获取 SmartDataHub 按设备聚合的数据统计。
 *
 * Returns:
 *     overall 与设备统计列表。
 */
export async function fetchDataDeviceStats() {
  const response = await http.get("/api/data/device-stats");
  return {
    overall: response.data?.overall || {},
    items: response.data?.items || []
  };
}

/**
 * 获取 SmartDataHub 数据资产列表。
 *
 * Args:
 *     filters: 资产筛选条件。
 *
 * Returns:
 *     数据资产列表与匹配总数。
 */
export async function fetchDataAssets(filters = {}) {
  const response = await http.get("/api/data/assets", {
    params: {
      device_id: filters.device_id || undefined,
      limit: filters.limit || 100
    }
  });
  return {
    items: response.data?.items || [],
    total: response.data?.total || 0
  };
}

/**
 * 获取指定数据资产的文件清单。
 *
 * Args:
 *     assetId: 数据资产 ID。
 *
 * Returns:
 *     文件明细列表。
 */
export async function fetchDataAssetFiles(assetId) {
  const response = await http.get(`/api/data/assets/${assetId}/files`, {
    params: { limit: 2000 }
  });
  return response.data?.items || [];
}
