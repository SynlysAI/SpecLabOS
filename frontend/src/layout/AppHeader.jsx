import React from "react";
import { Avatar, Button, Dropdown, Input, Space, Tag, Typography } from "antd";
import { BellOutlined, LogoutOutlined, SearchOutlined } from "@ant-design/icons";
import { useLocation, useNavigate } from "react-router-dom";

import { useAuth } from "../auth/AuthContext";

const { Text, Title } = Typography;

const HEADER_META = [
  {
    match: (pathname) => pathname === "/",
    title: "设备监控",
    subtitle: "集中查看实验设备状态、连通性与运行概览。"
  },
  {
    match: (pathname) => pathname.startsWith("/workflows/new"),
    title: "工作流编排",
    subtitle: "配置单设备工作流步骤、参数与提交流程。"
  },
  {
    match: (pathname) => pathname.startsWith("/runs/"),
    title: "运行详情",
    subtitle: "查看工作流执行明细、步骤时间线与接口响应结果。"
  },
  {
    match: (pathname) => pathname.startsWith("/runs"),
    title: "任务运行",
    subtitle: "追踪工作流运行记录、执行状态与目标设备。"
  },
  {
    match: (pathname) => pathname.startsWith("/logs"),
    title: "设备日志",
    subtitle: "检索设备事件、错误信息与关键操作记录。"
  },
  {
    match: (pathname) => pathname.startsWith("/tools/instruction-parser"),
    title: "树脂合成指令解析",
    subtitle: "将自然语言实验方案拆解为树脂合成设备可执行指令。"
  },
  {
    match: (pathname) => pathname.startsWith("/tools/science-data-assistant"),
    title: "科学数据助手",
    subtitle: "通过自然语言检索科学文献、化学数据与蛋白质分析资源。"
  },
  {
    match: (pathname) => pathname.startsWith("/tools"),
    title: "工具服务",
    subtitle: "树脂合成指令解析、实验方案智能拆解等实用工具。"
  }
];

/**
 * 顶部操作区组件。
 *
 * Returns:
 *     展示控制台标题、搜索、通知与当前登录人信息。
 */
export default function AppHeader() {
  const location = useLocation();
  const navigate = useNavigate();
  const { signOut, user } = useAuth();
  const headerMeta =
    HEADER_META.find((item) => item.match(location.pathname)) || HEADER_META[0];
  const username = user?.username || "未登录";
  const roleLabel = user?.role === "admin" ? "系统管理员" : "普通用户";
  const avatarText = username.slice(0, 1).toUpperCase();

  /**
   * 退出当前账号。
   */
  const handleLogout = () => {
    signOut();
    navigate("/login", { replace: true });
  };

  return (
    <div className="app-header">
      <div className="app-header-copy">
        <Title level={4} className="app-header-title">
          {headerMeta.title}
        </Title>
        <Text type="secondary" className="app-header-subtitle">
          {headerMeta.subtitle}
        </Text>
      </div>
      <Space size={16} className="app-header-actions">
        <Input
          allowClear
          prefix={<SearchOutlined />}
          placeholder="搜索设备、流程或日志"
          style={{ width: 280 }}
        />
        <Tag color="blue" bordered={false}>
          实验室网络已连接
        </Tag>
        <Button shape="circle" icon={<BellOutlined />} />
        <Dropdown
          trigger={["click"]}
          menu={{
            items: [
              {
                key: "logout",
                icon: <LogoutOutlined />,
                label: "退出登录",
                onClick: handleLogout
              }
            ]
          }}
        >
          <button className="app-header-user-button" type="button">
            <Space size={10} className="app-header-user">
              <Avatar style={{ backgroundColor: "#1f5eff" }}>{avatarText}</Avatar>
              <div className="app-header-user-meta">
                <Text strong className="app-header-user-name">
                  {username}
                </Text>
                <Text type="secondary">{roleLabel}</Text>
              </div>
            </Space>
          </button>
        </Dropdown>
      </Space>
    </div>
  );
}
