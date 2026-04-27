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
    <Layout className="app-shell">
      <Sider width={240} theme="light" className="app-shell-sider">
        <AppSidebar />
      </Sider>
      <Layout>
        <Header className="app-shell-header">
          <AppHeader />
        </Header>
        <Content className="app-shell-content">
          <div className="shell-content-panel">
            <Outlet />
          </div>
        </Content>
      </Layout>
    </Layout>
  );
}
