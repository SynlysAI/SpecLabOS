import React from "react";
import { Empty, List, Space, Typography } from "antd";

import StatusTag from "./StatusTag";

const { Paragraph, Text } = Typography;

/**
 * 运行步骤时间线组件。
 *
 * Args:
 *     steps: 运行步骤列表。
 *
 * Returns:
 *     展示步骤执行顺序、状态与时间信息。
 */
export default function RunStepTimeline({ steps }) {
  if (!steps?.length) {
    return <Empty description="暂无步骤执行记录" />;
  }

  return (
    <List
      dataSource={steps}
      renderItem={(step, index) => (
        <List.Item>
          <Space direction="vertical" size={4} style={{ width: "100%" }}>
            <Space style={{ justifyContent: "space-between", width: "100%" }} wrap>
              <Space>
                <Text strong>{`${index + 1}. ${step.name}`}</Text>
                <StatusTag status={step.status} />
              </Space>
              <Text type="secondary">{step.finished_at || step.started_at || "等待执行"}</Text>
            </Space>
            <Paragraph type="secondary" style={{ marginBottom: 0 }}>
              {step.description || "未提供步骤说明"}
            </Paragraph>
          </Space>
        </List.Item>
      )}
    />
  );
}
