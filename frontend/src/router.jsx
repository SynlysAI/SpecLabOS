import React, { Suspense, lazy } from "react";
import { createBrowserRouter } from "react-router-dom";

import AppShell from "./layout/AppShell";

const DeviceMonitorPage = lazy(() => import("./pages/DeviceMonitorPage"));
const WorkflowBuilderPage = lazy(() => import("./pages/WorkflowBuilderPage"));
const WorkflowRunsPage = lazy(() => import("./pages/WorkflowRunsPage"));
const WorkflowRunDetailPage = lazy(() => import("./pages/WorkflowRunDetailPage"));
const SystemLogsPage = lazy(() => import("./pages/SystemLogsPage"));
const ToolsPage = lazy(() => import("./pages/ToolsPage"));
const InstructionParserTab = lazy(() => import("./pages/InstructionParserTab"));
const ScienceDataAssistant = lazy(() => import("./pages/ScienceDataAssistant"));

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

export const router = createBrowserRouter([
  {
    path: "/",
    element: <AppShell />,
    children: [
      { index: true, element: withSuspense(<DeviceMonitorPage />) },
      {
        path: "workflows/new",
        element: withSuspense(<WorkflowBuilderPage />)
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
