import React from "react";
import { Button, Empty, Form, Input, Select, Space } from "antd";

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
export default function WorkflowStepForm({
  form,
  onSubmit,
  deviceOptions,
  actionOptions,
  selectedDeviceKey,
  onDeviceChange
}) {
  return (
    <Form form={form} layout="vertical" onFinish={onSubmit}>
      <Form.Item
        label="步骤名称"
        name="name"
        rules={[{ required: true, message: "请输入步骤名称" }]}
      >
        <Input placeholder="例如：nmr_2278 状态检查" />
      </Form.Item>
      <Form.Item
        label="目标设备"
        name="device_key"
        rules={[{ required: true, message: "请选择目标设备" }]}
      >
        <Select options={deviceOptions} placeholder="选择设备实例" onChange={onDeviceChange} />
      </Form.Item>
      <Form.Item
        label="设备动作"
        name="action_key"
        rules={[{ required: true, message: "请选择设备动作" }]}
      >
        <Select
          options={actionOptions}
          placeholder={selectedDeviceKey ? "选择设备动作" : "请先选择设备"}
          disabled={!selectedDeviceKey}
        />
      </Form.Item>
      <Form.Item label="执行说明" name="description">
        <Input.TextArea rows={4} placeholder="记录执行参数、预期结果或动作备注" />
      </Form.Item>
      {!selectedDeviceKey ? <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="请选择设备后再配置动作" /> : null}
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
