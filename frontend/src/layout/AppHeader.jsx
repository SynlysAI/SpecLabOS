import React from "react";
import { Avatar, Button, Input, Space, Tag, Typography } from "antd";
import { BellOutlined, SearchOutlined } from "@ant-design/icons";

const { Text, Title } = Typography;

/**
 * 顶部操作区组件。
 *
 * Returns:
 *     展示控制台标题、搜索、通知与当前登录人信息。
 */
export default function AppHeader() {
  return (
    <div
      style={{
        height: "100%",
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        gap: 16
      }}
    >
      <div>
        <Title level={4} style={{ margin: 0, fontSize: 18 }}>
          SpecLabOS 管理控制台
        </Title>
        <Text type="secondary">实验设备、流程编排与系统运行的统一入口</Text>
      </div>
      <Space size={16}>
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
        <Space size={10}>
          <Avatar style={{ backgroundColor: "#1f5eff" }}>A</Avatar>
          <div style={{ lineHeight: 1.2 }}>
            <Text strong style={{ display: "block" }}>
              Admin
            </Text>
            <Text type="secondary">系统管理员</Text>
          </div>
        </Space>
      </Space>
    </div>
  );
}
