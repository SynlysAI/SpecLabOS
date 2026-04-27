import React from "react";
import { Button, Space, Typography } from "antd";

const { Text, Title } = Typography;

/**
 * 页面工具栏组件。
 *
 * Args:
 *     title: 页面标题。
 *     subtitle: 页面副标题。
 *     extra: 右侧扩展操作区。
 *
 * Returns:
 *     页面头部标题与操作栏。
 */
export default function PageToolbar({ title, subtitle, extra }) {
  return (
    <div
      style={{
        display: "flex",
        justifyContent: "space-between",
        alignItems: "flex-start",
        gap: 16,
        marginBottom: 20
      }}
    >
      <div>
        <Title level={3} style={{ margin: 0, fontSize: 22 }}>
          {title}
        </Title>
        {subtitle ? (
          <Text type="secondary" style={{ display: "block", marginTop: 6 }}>
            {subtitle}
          </Text>
        ) : null}
      </div>
      <Space>
        {extra}
        <Button type="default">导出视图</Button>
      </Space>
    </div>
  );
}
