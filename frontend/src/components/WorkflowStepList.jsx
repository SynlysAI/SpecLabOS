import React from "react";
import { Button, Empty, List, Space, Typography } from "antd";

import StatusTag from "./StatusTag";

const { Paragraph, Text } = Typography;

/**
 * 工作流步骤列表组件。
 *
 * Args:
 *     steps: 当前步骤列表。
 *     onRemove: 删除步骤回调。
 *
 * Returns:
 *     展示当前编排步骤顺序的列表。
 */
export default function WorkflowStepList({ steps, onRemove }) {
  if (!steps.length) {
    return <Empty description="尚未添加步骤" />;
  }

  return (
    <List
      dataSource={steps}
      renderItem={(step, index) => (
        <List.Item
          actions={[
            <Button key="remove" type="link" danger onClick={() => onRemove(step.key)}>
              删除
            </Button>
          ]}
        >
          <Space direction="vertical" size={4} style={{ width: "100%" }}>
            <Space>
              <Text strong>{`${index + 1}. ${step.name}`}</Text>
              <StatusTag status="draft" label={step.typeLabel} />
            </Space>
            <Paragraph type="secondary" style={{ marginBottom: 0 }}>
              {step.description || "未填写执行说明"}
            </Paragraph>
          </Space>
        </List.Item>
      )}
    />
  );
}
