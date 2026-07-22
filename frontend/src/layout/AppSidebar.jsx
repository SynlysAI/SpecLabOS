import React, { useMemo, useState } from "react";
import { Button, Menu, Typography } from "antd";
import {
  AppstoreOutlined,
  ClusterOutlined,
  DashboardOutlined,
  DatabaseOutlined,
  FileSearchOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  SafetyCertificateOutlined,
  ToolOutlined
} from "@ant-design/icons";
import { useLocation, useNavigate } from "react-router-dom";

import { useAuth } from "../auth/AuthContext";

const BASE_MENU_ITEMS = [
  {
    key: "/",
    icon: <DashboardOutlined />,
    label: "设备监控"
  },
  {
    key: "/workflows",
    icon: <ClusterOutlined />,
    label: "工作流中心",
    children: [
      {
        key: "/workflows/local-builder",
        label: "本地编排"
      },
      {
        key: "/workflows/smartaccess-templates",
        label: "SmartAccess 模板"
      }
    ]
  },
  {
    key: "/tasks",
    icon: <AppstoreOutlined />,
    label: "任务中心",
    children: [
      {
        key: "/tasks/orchestration-runs",
        label: "编排任务"
      },
      {
        key: "/tasks/smartaccess-runs",
        label: "SmartAccess 任务"
      },
      {
        key: "/tasks/external-experiment-dispatches",
        label: "外部实验任务"
      }
    ]
  },
  {
    key: "/data/smartdatahub",
    icon: <DatabaseOutlined />,
    label: "数据中心"
  },
  {
    key: "/logs",
    icon: <FileSearchOutlined />,
    label: "设备日志"
  },
  {
    key: "/tools",
    icon: <ToolOutlined />,
    label: "工具服务",
    children: [
      {
        key: "/tools/instruction-parser",
        label: "树脂合成指令解析"
      },
      {
        key: "/tools/science-data-assistant",
        label: "科学数据助手"
      }
    ]
  }
];

const ADMIN_MENU_ITEMS = [
  {
    key: "/admin",
    icon: <SafetyCertificateOutlined />,
    label: "权限管理",
    children: [
      {
        key: "/admin/device-permissions",
        label: "设备权限"
      }
    ]
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
  const { user } = useAuth();

  const menuItems = useMemo(() => {
    const items = [...BASE_MENU_ITEMS];
    if (user?.role === "admin") {
      items.push(...ADMIN_MENU_ITEMS);
    }
    return items;
  }, [user?.role]);

  /** 展平所有菜单项（含子项），从中找出匹配当前路径的最深层 key。 */
  const allFlatItems = useMemo(
    () =>
      menuItems.flatMap(function flatten(item) {
        return item.children
          ? [item, ...item.children.flatMap(flatten)]
          : [item];
      }),
    [menuItems]
  );

  const selectedKey = useMemo(() => {
    let best = null;
    for (const item of allFlatItems) {
      if (item.key !== "/" && location.pathname.startsWith(item.key)) {
        if (!best || item.key.length > best.key.length) best = item;
      }
    }
    if (best) return best.key;
    return location.pathname === "/" ? "/" : undefined;
  }, [allFlatItems, location.pathname]);

  /** 默认展开包含当前选中项的父级菜单。 */
  const initialOpenKeys = useMemo(() => {
    const parents = [];
    for (const item of menuItems) {
      if (
        item.children &&
        item.children.some(function (child) {
          return allFlatItems.some(function (flat) {
            return flat.key === child.key && location.pathname.startsWith(flat.key);
          });
        })
      ) {
        parents.push(item.key);
      }
    }
    return parents;
  }, [location.pathname, allFlatItems]);

  const [openKeys, setOpenKeys] = useState(initialOpenKeys);

  return (
    <div className="sidebar-root">
      <div className="sidebar-topbar">
        <div className={`sidebar-brand ${collapsed ? "is-collapsed" : ""}`}>
          <div className="sidebar-brand-mark">
            <img src="/JG-logo.png" alt="JG Logo" style={{ width: '100%', height: '100%', objectFit: 'contain' }} />
          </div>
          {!collapsed ? (
            <div className="sidebar-brand-copy">
              <Text className="sidebar-brand-product">SpecLabOS</Text>
              <Text type="secondary" className="sidebar-brand-text">
                实验管理平台 — 实验设备、流程编排与运行监控的一体化工作台
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
        openKeys={collapsed ? [] : openKeys}
        onOpenChange={setOpenKeys}
        items={menuItems}
        onClick={({ key, keyPath }) => {
          // 仅有 children 的父级 item 不触发导航
          const item = menuItems.flatMap((i) => (i.children ? i.children : [i])).find(
            (i) => i.key === key
          );
          if (item && !item.children) navigate(key);
        }}
        className="sidebar-menu"
        style={{ borderInlineEnd: "none", background: "transparent" }}
      />
      <div className="sidebar-version">
        {!collapsed && <Text type="secondary">版本 v1.0.0</Text>}
      </div>
    </div>
  );
}
