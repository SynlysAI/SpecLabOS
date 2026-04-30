import React, { useState } from "react";
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
  const [collapsed, setCollapsed] = useState(false);

  return (
    <Layout className="app-shell">
      <Sider
        width={256}
        collapsed={collapsed}
        collapsedWidth={92}
        trigger={null}
        theme="light"
        className="app-shell-sider"
      >
        <AppSidebar
          collapsed={collapsed}
          onToggle={() => setCollapsed((current) => !current)}
        />
      </Sider>
      <Layout>
        <Header className="app-shell-header">
          <AppHeader />
        </Header>
        <Content className="app-shell-content">
          <div className="shell-content-layout">
            <Outlet />
          </div>
        </Content>
      </Layout>
    </Layout>
  );
}
