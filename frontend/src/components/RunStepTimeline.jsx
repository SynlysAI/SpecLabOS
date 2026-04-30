import React, { useState } from "react";
import { Button, Empty, List, Modal, Space, Typography } from "antd";

import StatusTag from "./StatusTag";

const { Paragraph, Text } = Typography;


/**
 * 将步骤结果格式化为可读 JSON 文本。
 *
 * Args:
 *     value: 步骤执行结果。
 *
 * Returns:
 *     格式化后的展示文本。
 */
function formatStepResult(value) {
  if (value === undefined || value === null) {
    return "暂无响应数据";
  }
  if (typeof value === "string") {
    return value;
  }
  try {
    return JSON.stringify(value, null, 2);
  } catch (error) {
    return String(value);
  }
}

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
  const [selectedStep, setSelectedStep] = useState(null);

  if (!steps?.length) {
    return <Empty description="暂无步骤执行记录" />;
  }

  return (
    <>
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
                <Space>
                  <Text type="secondary">
                    {step.finished_at || step.started_at || "等待执行"}
                  </Text>
                  <Button
                    type="link"
                    size="small"
                    onClick={() => setSelectedStep({ ...step, index: index + 1 })}
                  >
                    查看响应
                  </Button>
                </Space>
              </Space>
              <Paragraph type="secondary" style={{ marginBottom: 0 }}>
                {step.description || "未提供步骤说明"}
              </Paragraph>
            </Space>
          </List.Item>
        )}
      />
      <Modal
        title={
          selectedStep ? `步骤 ${selectedStep.index}: ${selectedStep.name} 响应结果` : "步骤响应结果"
        }
        open={Boolean(selectedStep)}
        footer={null}
        onCancel={() => setSelectedStep(null)}
        width={720}
      >
        <pre
          style={{
            margin: 0,
            padding: 16,
            borderRadius: 12,
            background: "#f7f8fc",
            overflowX: "auto",
            whiteSpace: "pre-wrap",
            wordBreak: "break-word",
            fontSize: 13,
            lineHeight: 1.6,
          }}
        >
          {formatStepResult(selectedStep?.result)}
        </pre>
      </Modal>
    </>
  );
}
