import React from "react";
import { Button, Menu, Typography } from "antd";
import {
  AppstoreOutlined,
  ClusterOutlined,
  DashboardOutlined,
  FileSearchOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined
} from "@ant-design/icons";
import { useLocation, useNavigate } from "react-router-dom";

const MENU_ITEMS = [
  {
    key: "/",
    icon: <DashboardOutlined />,
    label: "设备监控"
  },
  {
    key: "/workflows/new",
    icon: <ClusterOutlined />,
    label: "工作流编排"
  },
  {
    key: "/runs",
    icon: <AppstoreOutlined />,
    label: "任务运行"
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
export default function AppSidebar({ collapsed, onToggle }) {
  const navigate = useNavigate();
  const location = useLocation();
  const selectedKey =
    MENU_ITEMS.find(
      (item) => item.key !== "/" && location.pathname.startsWith(item.key)
    )?.key ||
    (location.pathname === "/" ? "/" : undefined);

  return (
    <div className="sidebar-root">
      <div className="sidebar-topbar">
        <div className={`sidebar-brand ${collapsed ? "is-collapsed" : ""}`}>
          <div className="sidebar-brand-mark">S</div>
          {!collapsed ? (
            <div className="sidebar-brand-copy">
              <Text className="sidebar-brand-product">SpecLabOS</Text>
              <Text type="secondary" className="sidebar-brand-text">
                实验设备、流程编排与运行监控的一体化工作台
              </Text>
            </div>
          ) : null}
        </div>
        <Button
          type="text"
          shape="circle"
          icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
          onClick={onToggle}
          className="sidebar-toggle"
          aria-label={collapsed ? "展开侧边栏" : "收起侧边栏"}
        />
      </div>
      <Menu
        mode="inline"
        inlineCollapsed={collapsed}
        selectedKeys={selectedKey ? [selectedKey] : []}
        items={MENU_ITEMS}
        onClick={({ key }) => navigate(key)}
        className="sidebar-menu"
        style={{ borderInlineEnd: "none", background: "transparent" }}
      />
      <div className="sidebar-version">
        {!collapsed && <Text type="secondary">v1.0.0</Text>}
      </div>
    </div>
  );
}
