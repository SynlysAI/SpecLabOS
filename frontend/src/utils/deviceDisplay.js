/**
 * 格式化设备接入模式。
 *
 * Args:
 *     adapterType: 设备适配器类型。
 *
 * Returns:
 *     前端展示用接入模式文本。
 */
export function formatDeviceAccessMode(adapterType) {
  if (adapterType === "smartaccess") return "SmartAccess";
  if (adapterType === "local") return "本地接入";
  if (adapterType === "api") return "API 接入";
  return "API 接入";
}
