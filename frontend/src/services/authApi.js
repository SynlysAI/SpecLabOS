import { http } from "./http";

/**
 * 登录并获取统一认证 token。
 *
 * Args:
 *     params: 登录用户名和密码。
 *
 * Returns:
 *     登录响应 Promise。
 */
export function login(params) {
  return http.post("/api/v1/auth/login", params);
}

/**
 * 使用 AI4MS 邀请码注册账号。
 *
 * Args:
 *     params: 邀请码、用户名、密码和单位名称。
 *
 * Returns:
 *     注册响应 Promise。
 */
export function register(params) {
  return http.post("/api/v1/auth/register", params);
}

/**
 * 获取当前登录用户状态。
 *
 * Returns:
 *     当前用户状态响应 Promise。
 */
export function getMe() {
  return http.get("/api/v1/auth/me");
}
