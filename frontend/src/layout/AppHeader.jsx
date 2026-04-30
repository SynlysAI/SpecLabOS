import React from "react";
import { Avatar, Button, Input, Space, Tag, Typography } from "antd";
import { BellOutlined, SearchOutlined } from "@ant-design/icons";
import { useLocation } from "react-router-dom";

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
    title: "系统日志",
    subtitle: "检索平台事件、错误信息与关键操作记录。"
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
  const headerMeta =
    HEADER_META.find((item) => item.match(location.pathname)) || HEADER_META[0];

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
        <Space size={10} className="app-header-user">
          <Avatar style={{ backgroundColor: "#1f5eff" }}>A</Avatar>
          <div className="app-header-user-meta">
            <Text strong className="app-header-user-name">
              Admin
            </Text>
            <Text type="secondary">系统管理员</Text>
          </div>
        </Space>
      </Space>
    </div>
  );
}
