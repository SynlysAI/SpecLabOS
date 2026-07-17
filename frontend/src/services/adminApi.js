import { http } from "./http";

/**
 * 拉取全部用户列表(管理员视角)。
 *
 * Returns:
 *     用户摘要信息列表 Promise。
 */
export function listUsers() {
  return http.get("/api/admin/users").then((response) => response.data);
}

/**
 * 查询某用户当前可控的设备列表。
 *
 * Args:
 *     userId: 用户唯一 ID。
 *
 * Returns:
 *     包含 user_id / username / role / device_keys 的对象 Promise。
 */
export function getUserDevices(userId) {
  return http
    .get(`/api/admin/users/${userId}/devices`)
    .then((response) => response.data);
}

/**
 * 覆盖式设置某用户的可控设备集合。
 *
 * Args:
 *     userId: 被授权用户 ID。
 *     deviceKeys: 新的设备标识完整列表。
 *
 * Returns:
 *     更新后的用户权限对象 Promise。
 */
export function replaceUserDevices(userId, deviceKeys) {
  return http
    .put(`/api/admin/users/${userId}/devices`, { device_keys: deviceKeys })
    .then((response) => response.data);
}

/**
 * 授予用户对单个设备的 control 权限(幂等)。
 *
 * Args:
 *     userId: 被授权用户 ID。
 *     deviceKey: 设备唯一标识。
 *
 * Returns:
 *     更新后的用户权限对象 Promise。
 */
export function grantUserDevice(userId, deviceKey) {
  return http
    .post(`/api/admin/users/${userId}/devices/${deviceKey}`)
    .then((response) => response.data);
}

/**
 * 撤销用户对单个设备的 control 权限。
 *
 * Args:
 *     userId: 用户唯一 ID。
 *     deviceKey: 设备唯一标识。
 *
 * Returns:
 *     更新后的用户权限对象 Promise。
 */
export function revokeUserDevice(userId, deviceKey) {
  return http
    .delete(`/api/admin/users/${userId}/devices/${deviceKey}`)
    .then((response) => response.data);
}

/**
 * 查询某设备授权给了哪些用户。
 *
 * Args:
 *     deviceKey: 设备唯一标识。
 *
 * Returns:
 *     包含 device_key / user_ids 的对象 Promise。
 */
export function getDeviceUsers(deviceKey) {
  return http
    .get(`/api/admin/devices/${deviceKey}/users`)
    .then((response) => response.data);
}

/**
 * 覆盖式设置某设备的授权用户集合。
 *
 * Args:
 *     deviceKey: 设备唯一标识。
 *     userIds: 新的用户 ID 完整列表。
 *
 * Returns:
 *     更新后的设备权限对象 Promise。
 */
export function replaceDeviceUsers(deviceKey, userIds) {
  return http
    .put(`/api/admin/devices/${deviceKey}/users`, { user_ids: userIds })
    .then((response) => response.data);
}
