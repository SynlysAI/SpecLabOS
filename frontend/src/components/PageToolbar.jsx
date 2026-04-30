import React from "react";
import { Space, Typography } from "antd";

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
  if (!title && !subtitle) {
    return extra ? (
      <div className="page-toolbar page-toolbar-actions-only">
        <div className="page-toolbar-actions">
          <Space wrap>{extra}</Space>
        </div>
      </div>
    ) : null;
  }

  return (
    <div className="page-toolbar">
      <div className="page-toolbar-copy">
        <Title level={3} className="page-toolbar-title">
          {title}
        </Title>
        {subtitle ? (
          <Text type="secondary" className="page-toolbar-subtitle">
            {subtitle}
          </Text>
        ) : null}
      </div>
      {extra ? (
        <div className="page-toolbar-actions">
          <Space wrap>{extra}</Space>
        </div>
      ) : null}
    </div>
  );
}
