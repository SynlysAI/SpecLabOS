import { http } from "./http";

/**
 * 获取设备列表。
 *
 * Returns:
 *     设备列表数据。
 */
export async function fetchDevices() {
  const response = await http.get("/api/devices");
  return response.data.items;
}

/**
 * 获取单个设备详情。
 *
 * Args:
 *     deviceKey: 设备唯一标识。
 *
 * Returns:
 *     设备详情数据。
 */
export async function fetchDeviceDetail(deviceKey) {
  const response = await http.get(`/api/devices/${deviceKey}`);
  return response.data;
}

/**
 * 解析设备图片 URL。
 *
 * Args:
 *     imageUrl: 后端返回的图片路径。
 *
 * Returns:
 *     浏览器可直接访问的图片地址。
 */
export function resolveDeviceImageUrl(imageUrl) {
  if (!imageUrl) {
    return "";
  }
  const baseUrl =
    import.meta.env.VITE_API_BASE_URL ||
    (import.meta.env.DEV ? "http://127.0.0.1:8000" : "");
  return `${baseUrl}${imageUrl}`;
}
