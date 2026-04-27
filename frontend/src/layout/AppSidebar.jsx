import React from "react";
import { Menu, Typography } from "antd";
import {
  AppstoreOutlined,
  ClusterOutlined,
  DashboardOutlined,
  FileSearchOutlined
} from "@ant-design/icons";
import { useLocation, useNavigate } from "react-router-dom";

const MENU_ITEMS = [
  {
    key: "/",
    icon: <DashboardOutlined />,
    label: "设备监控总览"
  },
  {
    key: "/workflows/new",
    icon: <ClusterOutlined />,
    label: "新建工作流"
  },
  {
    key: "/runs",
    icon: <AppstoreOutlined />,
    label: "运行记录"
  },
  {
    key: "/logs",
    icon: <FileSearchOutlined />,
    label: "系统日志"
  }
];

const { Text, Title } = Typography;

/**
 * 管理台侧边导航组件。
 *
 * Returns:
 *     提供核心模块导航入口。
 */
export default function AppSidebar() {
  const navigate = useNavigate();
  const location = useLocation();
  const selectedKey = MENU_ITEMS.find((item) =>
    location.pathname === "/"
      ? item.key === "/"
      : location.pathname.startsWith(item.key)
  )?.key;

  return (
    <div style={{ height: "100%", padding: "20px 16px 16px" }}>
      <div style={{ padding: "4px 12px 20px" }}>
        <Text
          style={{
            display: "block",
            color: "#1f5eff",
            fontSize: 12,
            fontWeight: 700,
            letterSpacing: "0.08em"
          }}
        >
          SPECLABOS
        </Text>
        <Title level={5} style={{ margin: "8px 0 4px" }}>
          企业后台
        </Title>
        <Text type="secondary">统一管理实验设备与自动化流程</Text>
      </div>
      <Menu
        mode="inline"
        selectedKeys={selectedKey ? [selectedKey] : []}
        items={MENU_ITEMS}
        onClick={({ key }) => navigate(key)}
        style={{ borderInlineEnd: "none", background: "transparent" }}
      />
    </div>
  );
}
