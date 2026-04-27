import React from "react";
import { Button, Form, Input, Select, Space } from "antd";

const STEP_TYPE_OPTIONS = [
  { label: "采集", value: "collect" },
  { label: "分析", value: "analyze" },
  { label: "导出", value: "export" }
];

/**
 * 工作流步骤表单组件。
 *
 * Args:
 *     form: 表单实例。
 *     onSubmit: 提交回调。
 *
 * Returns:
 *     用于添加单个工作流步骤的表单。
 */
export default function WorkflowStepForm({ form, onSubmit }) {
  return (
    <Form form={form} layout="vertical" onFinish={onSubmit} initialValues={{ type: "collect" }}>
      <Form.Item
        label="步骤名称"
        name="name"
        rules={[{ required: true, message: "请输入步骤名称" }]}
      >
        <Input placeholder="例如：样品加载" />
      </Form.Item>
      <Form.Item
        label="动作类型"
        name="type"
        rules={[{ required: true, message: "请选择动作类型" }]}
      >
        <Select options={STEP_TYPE_OPTIONS} />
      </Form.Item>
      <Form.Item label="执行说明" name="description">
        <Input.TextArea rows={4} placeholder="记录该步骤的目标或参数摘要" />
      </Form.Item>
      <Space>
        <Button type="primary" htmlType="submit">
          添加步骤
        </Button>
        <Button htmlType="button" onClick={() => form.resetFields()}>
          清空
        </Button>
      </Space>
    </Form>
  );
}
