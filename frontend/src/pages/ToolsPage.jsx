import React from "react";
import { Typography } from "antd";
import { ToolOutlined } from "@ant-design/icons";
import { Outlet, useLocation } from "react-router-dom";

const { Text, Title } = Typography;

/**
 * 工具服务父页签容器。
 *
 * Returns:
 *     提供工具服务模块的入口介绍（默认页）或子路由内容渲染。
 */
export default function ToolsPage() {
  const location = useLocation();

  const isRoot = location.pathname === "/tools";

  return (
    <section className="page-section">
      {isRoot && (
        <div style={{ textAlign: "center", padding: "80px 0" }}>
          <ToolOutlined style={{ fontSize: 48, color: "#1677ff", marginBottom: 24 }} />
          <Title level={3}>工具服务</Title>
          <Text type="secondary">
            请从左侧菜单选择具体工具，例如"树脂合成指令解析"。
          </Text>
        </div>
      )}
      <Outlet />
    </section>
  );
}
