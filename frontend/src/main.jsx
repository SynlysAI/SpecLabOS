import React from "react";
import ReactDOM from "react-dom/client";
import { ConfigProvider } from "antd";
import { RouterProvider } from "react-router-dom";

import { AuthProvider } from "./auth/AuthContext";
import App from "./App";
import { router } from "./router";
import "./styles/global.css";

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <ConfigProvider
      theme={{
        token: {
          colorPrimary: "#1f5eff",
          borderRadius: 10,
          colorBgLayout: "#edf2f7",
          colorText: "#1f2937",
          fontFamily: '"Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif'
        }
      }}
    >
      <App>
        <AuthProvider>
          <RouterProvider router={router} />
        </AuthProvider>
      </App>
    </ConfigProvider>
  </React.StrictMode>
);
