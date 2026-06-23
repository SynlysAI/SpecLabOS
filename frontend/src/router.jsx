import React, { Suspense, lazy } from "react";
import { createBrowserRouter, Navigate, useLocation } from "react-router-dom";

import { useAuth } from "./auth/AuthContext";
import AppShell from "./layout/AppShell";

const DeviceMonitorPage = lazy(() => import("./pages/DeviceMonitorPage"));
const WorkflowBuilderPage = lazy(() => import("./pages/WorkflowBuilderPage"));
const SmartAccessTemplatesPage = lazy(() => import("./pages/SmartAccessTemplatesPage"));
const WorkflowRunsPage = lazy(() => import("./pages/WorkflowRunsPage"));
const WorkflowRunDetailPage = lazy(() => import("./pages/WorkflowRunDetailPage"));
const SystemLogsPage = lazy(() => import("./pages/SystemLogsPage"));
const ToolsPage = lazy(() => import("./pages/ToolsPage"));
const InstructionParserTab = lazy(() => import("./pages/InstructionParserTab"));
const ScienceDataAssistant = lazy(() => import("./pages/ScienceDataAssistant"));
const LoginPage = lazy(() => import("./pages/LoginPage"));
const RegisterPage = lazy(() => import("./pages/RegisterPage"));

/**
 * 页面懒加载包装组件。
 *
 * Args:
 *     children: 需要在路由中渲染的页面组件。
 *
 * Returns:
 *     带有最小加载占位的页面内容。
 */
function withSuspense(children) {
  return (
    <Suspense
      fallback={
        <section className="page-section">
          <p className="page-subheading">页面加载中...</p>
        </section>
      }
    >
      {children}
    </Suspense>
  );
}

/**
 * 业务页面鉴权守卫。
 *
 * Returns:
 *     已登录时返回主布局，否则跳转登录页。
 */
function ProtectedShell() {
  const location = useLocation();
  const { initialized, isAuthenticated } = useAuth();

  if (!initialized) {
    return (
      <section className="auth-loading">
        <p>正在校验登录状态...</p>
      </section>
    );
  }
  if (!isAuthenticated) {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }
  return <AppShell />;
}

/**
 * 访客页面守卫。
 *
 * Args:
 *     children: 登录或注册页面。
 *
 * Returns:
 *     未登录时返回子页面，已登录时回到首页。
 */
function GuestOnly({ children }) {
  const { initialized, isAuthenticated } = useAuth();

  if (!initialized) {
    return (
      <section className="auth-loading">
        <p>正在校验登录状态...</p>
      </section>
    );
  }
  if (isAuthenticated) {
    return <Navigate to="/" replace />;
  }
  return children;
}

export const router = createBrowserRouter([
  {
    path: "/login",
    element: withSuspense(
      <GuestOnly>
        <LoginPage />
      </GuestOnly>
    )
  },
  {
    path: "/register",
    element: withSuspense(
      <GuestOnly>
        <RegisterPage />
      </GuestOnly>
    )
  },
  {
    path: "/",
    element: <ProtectedShell />,
    children: [
      { index: true, element: withSuspense(<DeviceMonitorPage />) },
      {
        path: "workflows/new",
        element: withSuspense(<WorkflowBuilderPage />)
      },
      {
        path: "smartaccess/templates",
        element: withSuspense(<SmartAccessTemplatesPage />)
      },
      { path: "runs", element: withSuspense(<WorkflowRunsPage />) },
      {
        path: "runs/:runId",
        element: withSuspense(<WorkflowRunDetailPage />)
      },
      { path: "logs", element: withSuspense(<SystemLogsPage />) },
      {
        path: "tools",
        element: withSuspense(<ToolsPage />),
        children: [
          {
            path: "instruction-parser",
            element: withSuspense(<InstructionParserTab />)
          },
          {
            path: "science-data-assistant",
            element: withSuspense(<ScienceDataAssistant />)
          }
        ]
      }
    ]
  }
]);
