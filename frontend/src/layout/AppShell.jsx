import React from "react";
import { Layout } from "antd";
import { Outlet } from "react-router-dom";

import AppHeader from "./AppHeader";
import AppSidebar from "./AppSidebar";

const { Sider, Header, Content } = Layout;

/**
 * 管理台主布局组件。
 *
 * Returns:
 *     提供后台侧栏、顶部操作区和主内容区布局。
 */
export default function AppShell() {
  return (
    <Layout style={{ minHeight: "100vh" }}>
      <Sider
        width={240}
        theme="light"
        style={{
          borderRight: "1px solid #d9e2ec",
          background: "#f8fafc"
        }}
      >
        <AppSidebar />
      </Sider>
      <Layout>
        <Header
          style={{
            height: 72,
            padding: "0 28px",
            borderBottom: "1px solid #d9e2ec",
            background: "rgba(248, 250, 252, 0.94)"
          }}
        >
          <AppHeader />
        </Header>
        <Content style={{ padding: 20, background: "transparent" }}>
          <div className="shell-content-panel">
            <Outlet />
          </div>
        </Content>
      </Layout>
    </Layout>
  );
}
