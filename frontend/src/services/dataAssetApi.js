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
      keyword: filters.keyword || undefined,
      device_id: filters.device_id || undefined,
      collector_id: filters.collector_id || undefined,
      data_type: filters.data_type && filters.data_type !== "all" ? filters.data_type : undefined,
      asset_kind: filters.asset_kind && filters.asset_kind !== "all" ? filters.asset_kind : undefined,
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

/**
 * 删除单个数据文件及其存储对象。
 *
 * Args:
 *     fileId: 数据文件 ID。
 *
 * Returns:
 *     删除摘要信息。
 */
export async function deleteDataAssetFile(fileId) {
  const response = await http.delete(`/api/data/files/${fileId}`);
  return response.data || {};
}

/**
 * 删除整个数据资产及其全部文件。
 *
 * Args:
 *     assetId: 数据资产 ID。
 *
 * Returns:
 *     删除摘要信息。
 */
export async function deleteDataAsset(assetId) {
  const response = await http.delete(`/api/data/assets/${assetId}`);
  return response.data || {};
}

/**
 * 下载单个数据文件到本地。
 *
 * Args:
 *     file: 含 file_id 和 filename 的文件记录。
 */
export async function downloadDataAssetFile(file) {
  const response = await http.get(`/api/data/files/${file.file_id}/download`, {
    responseType: "blob",
    timeout: 0
  });
  saveBlobAsFile(response.data, file.filename || file.file_id);
}

/**
 * 下载资产压缩包（zip）到本地。
 *
 * Args:
 *     asset: 含 asset_id 的资产记录。
 *     zipName: 保存使用的压缩包文件名。
 */
export async function downloadDataAssetZip(asset, zipName) {
  const response = await http.get(`/api/data/assets/${asset.asset_id}/download`, {
    responseType: "blob",
    timeout: 0
  });
  saveBlobAsFile(response.data, zipName);
}

/**
 * 把 Blob 内容保存为本地文件。
 *
 * Args:
 *     blob: 响应二进制内容。
 *     filename: 保存使用的文件名。
 */
function saveBlobAsFile(blob, filename) {
  const SAFE_FILENAME_PATTERN = /[\\/:*?"<>|]/g;
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename.replace(SAFE_FILENAME_PATTERN, "_") || "download";
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}
