import React, { createContext, useContext, useEffect, useState } from "react";

import { AUTH_TOKEN_KEY } from "../services/http";
import * as authApi from "../services/authApi";

const AuthContext = createContext(null);

/**
 * 从 AI4MS 门户跳转 hash 中接收 token。
 *
 * Returns:
 *     成功接收时返回 true，否则返回 false。
 */
function acceptPortalToken() {
  const hash = window.location.hash || "";
  const params = new URLSearchParams(hash.replace(/^#/, ""));
  const token = params.get("token");
  if (!token) return false;

  sessionStorage.setItem(AUTH_TOKEN_KEY, token);
  params.delete("token");
  const nextHash = params.toString();
  const nextUrl = `${window.location.pathname}${window.location.search}${
    nextHash ? `#${nextHash}` : ""
  }`;
  window.history.replaceState(null, "", nextUrl);
  return true;
}

/**
 * 提取接口响应的 data 字段。
 *
 * Args:
 *     response: Axios 响应对象。
 *
 * Returns:
 *     业务响应 data 字段。
 */
function extractData(response) {
  return response.data?.data;
}

/**
 * 统一认证状态提供者。
 *
 * Args:
 *     children: 子组件。
 *
 * Returns:
 *     包含认证上下文的 React 节点。
 */
export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [authEnabled, setAuthEnabled] = useState(true);
  const [initialized, setInitialized] = useState(false);
  const [loading, setLoading] = useState(false);

  const refreshCurrentUser = async () => {
    const response = await authApi.getMe();
    const data = extractData(response);
    setAuthEnabled(data.auth_enabled);
    setUser(data.user);
    return data.user;
  };

  useEffect(() => {
    let ignore = false;
    acceptPortalToken();

    async function initialize() {
      try {
        const response = await authApi.getMe();
        if (ignore) return;
        const data = extractData(response);
        setAuthEnabled(data.auth_enabled);
        setUser(data.user);
      } catch {
        if (!ignore) {
          setAuthEnabled(true);
          setUser(null);
        }
      } finally {
        if (!ignore) setInitialized(true);
      }
    }

    const handleExpired = () => setUser(null);
    window.addEventListener("speclabos-auth-expired", handleExpired);
    initialize();

    return () => {
      ignore = true;
      window.removeEventListener("speclabos-auth-expired", handleExpired);
    };
  }, []);

  const signIn = async (username, password) => {
    setLoading(true);
    try {
      const response = await authApi.login({ username, password });
      const data = extractData(response);
      sessionStorage.setItem(AUTH_TOKEN_KEY, data.token);
      setUser({ ...data.user, status: "active" });
    } finally {
      setLoading(false);
    }
  };

  const signUp = async (params) => {
    setLoading(true);
    try {
      const response = await authApi.register(params);
      const data = extractData(response);
      sessionStorage.setItem(AUTH_TOKEN_KEY, data.token);
      setUser({ ...data.user, status: "active" });
    } finally {
      setLoading(false);
    }
  };

  const signOut = () => {
    sessionStorage.removeItem(AUTH_TOKEN_KEY);
    setUser(null);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        authEnabled,
        initialized,
        loading,
        isAuthenticated: !authEnabled || Boolean(user),
        refreshCurrentUser,
        signIn,
        signUp,
        signOut
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

/**
 * 读取统一认证上下文。
 *
 * Returns:
 *     认证上下文对象。
 */
export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth 必须在 AuthProvider 内使用");
  }
  return context;
}
