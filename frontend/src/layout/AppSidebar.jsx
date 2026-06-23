import React, { useMemo, useState } from "react";
import { Button, Menu, Typography } from "antd";
import {
  AppstoreOutlined,
  ClusterOutlined,
  CloudServerOutlined,
  DashboardOutlined,
  FileSearchOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  ToolOutlined
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
    key: "/smartaccess/templates",
    icon: <CloudServerOutlined />,
    label: "SmartAccess 模板"
  },
  {
    key: "/runs",
    icon: <AppstoreOutlined />,
    label: "任务运行"
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

  /** 展平所有菜单项（含子项），从中找出匹配当前路径的最深层 key。 */
  const allFlatItems = useMemo(
    () =>
      MENU_ITEMS.flatMap(function flatten(item) {
        return item.children
          ? [item, ...item.children.flatMap(flatten)]
          : [item];
      }),
    []
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
    for (const item of MENU_ITEMS) {
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
        items={MENU_ITEMS}
        onClick={({ key, keyPath }) => {
          // 仅有 children 的父级 item 不触发导航
          const item = MENU_ITEMS.flatMap((i) => (i.children ? i.children : [i])).find(
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
