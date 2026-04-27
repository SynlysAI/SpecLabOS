import React from "react";
import { createBrowserRouter } from "react-router-dom";

import AppShell from "./layout/AppShell";
import DeviceMonitorPage from "./pages/DeviceMonitorPage";
import WorkflowBuilderPage from "./pages/WorkflowBuilderPage";
import WorkflowRunsPage from "./pages/WorkflowRunsPage";
import SystemLogsPage from "./pages/SystemLogsPage";

export const router = createBrowserRouter([
  {
    path: "/",
    element: <AppShell />,
    children: [
      { index: true, element: <DeviceMonitorPage /> },
      { path: "workflows/new", element: <WorkflowBuilderPage /> },
      { path: "runs", element: <WorkflowRunsPage /> },
      { path: "logs", element: <SystemLogsPage /> }
    ]
  }
]);
