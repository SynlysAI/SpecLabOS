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
