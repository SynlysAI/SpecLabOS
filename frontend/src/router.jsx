import React, { Suspense, lazy } from "react";
import { createBrowserRouter, Navigate, useLocation } from "react-router-dom";

import { useAuth } from "./auth/AuthContext";
import AppShell from "./layout/AppShell";

const DeviceMonitorPage = lazy(() => import("./pages/DeviceMonitorPage"));
const WorkflowCenterPage = lazy(() => import("./pages/WorkflowCenterPage"));
const TaskCenterPage = lazy(() => import("./pages/TaskCenterPage"));
const WorkflowRunDetailPage = lazy(() => import("./pages/WorkflowRunDetailPage"));
const SmartDataHubOverviewPage = lazy(() => import("./pages/SmartDataHubOverviewPage"));
const SystemLogsPage = lazy(() => import("./pages/SystemLogsPage"));
const ToolsPage = lazy(() => import("./pages/ToolsPage"));
const InstructionParserTab = lazy(() => import("./pages/InstructionParserTab"));
const ScienceDataAssistant = lazy(() => import("./pages/ScienceDataAssistant"));
const LoginPage = lazy(() => import("./pages/LoginPage"));
const RegisterPage = lazy(() => import("./pages/RegisterPage"));
const DevicePermissionsPage = lazy(() => import("./pages/admin/DevicePermissionsPage"));

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

/**
 * 管理员页面守卫。
 *
 * Args:
 *     children: 仅管理员可访问的页面。
 *
 * Returns:
 *     已登录且为管理员时返回子页面,否则回到首页。
 */
function RequireAdmin({ children }) {
  const { initialized, isAuthenticated, user } = useAuth();

  if (!initialized) {
    return (
      <section className="auth-loading">
        <p>正在校验登录状态...</p>
      </section>
    );
  }
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }
  if (user?.role !== "admin") {
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
      { path: "workflows", element: <Navigate to="/workflows/local-builder" replace /> },
      { path: "workflows/new", element: <Navigate to="/workflows/local-builder" replace /> },
      {
        path: "workflows/:tabKey",
        element: withSuspense(<WorkflowCenterPage />)
      },
      { path: "tasks", element: <Navigate to="/tasks/orchestration-runs" replace /> },
      { path: "tasks/device-runs", element: <Navigate to="/tasks/orchestration-runs" replace /> },
      {
        path: "tasks/:tabKey",
        element: withSuspense(<TaskCenterPage />)
      },
      {
        path: "smartaccess/templates",
        element: <Navigate to="/workflows/smartaccess-templates" replace />
      },
      {
        path: "smartaccess/runs",
        element: <Navigate to="/tasks/smartaccess-runs" replace />
      },
      {
        path: "smartaccess/runs/:runId",
        element: withSuspense(<WorkflowRunDetailPage />)
      },
      { path: "runs", element: <Navigate to="/tasks/orchestration-runs" replace /> },
      {
        path: "runs/:runId",
        element: withSuspense(<WorkflowRunDetailPage />)
      },
      { path: "data", element: <Navigate to="/data/smartdatahub" replace /> },
      { path: "data/smartdatahub", element: withSuspense(<SmartDataHubOverviewPage />) },
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
      },
      {
        path: "admin/device-permissions",
        element: (
          <RequireAdmin>
            {withSuspense(<DevicePermissionsPage />)}
          </RequireAdmin>
        )
      }
    ]
  }
]);
