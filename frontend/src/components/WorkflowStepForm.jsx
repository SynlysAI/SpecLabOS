import React from "react";
import { Button, Empty, Form, Input, InputNumber, Select, Space, Switch } from "antd";

/**
 * 将参数类型映射到对应的输入组件。
 *
 * Args:
 *     field: 动作参数定义。
 *
 * Returns:
 *     对应的表单输入组件。
 */
function renderFieldInput(field) {
  if (field.type === "number") {
    return <InputNumber style={{ width: "100%" }} placeholder={`请输入${field.name}`} />;
  }
  if (field.type === "boolean") {
    return <Switch />;
  }
  if (field.type === "json") {
    return (
      <Input.TextArea
        rows={5}
        placeholder={`请输入 ${field.name} 的 JSON 内容`}
      />
    );
  }
  return <Input placeholder={`请输入${field.name}`} />;
}

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
  actionOptions,
  selectedDeviceKey,
  actionSchemas
}) {
  const selectedActionKey = Form.useWatch("action_key", form);
  const currentSchema = actionSchemas[selectedActionKey] || [];

  return (
    <Form form={form} layout="vertical" onFinish={onSubmit}>
      <Form.Item
        label="步骤名称"
        name="name"
        rules={[{ required: true, message: "请输入步骤名称" }]}
      >
        <Input placeholder="例如：Raman 采集任务" />
      </Form.Item>
      <Form.Item
        label="设备动作"
        name="action_key"
        rules={[{ required: true, message: "请选择设备动作" }]}
      >
        <Select
          options={actionOptions}
          placeholder={selectedDeviceKey ? "选择设备动作" : "请先选择目标设备"}
          disabled={!selectedDeviceKey}
        />
      </Form.Item>
      {currentSchema.map((field) => (
        <Form.Item
          key={field.name}
          label={field.description ? `${field.name} · ${field.description}` : field.name}
          name={["action_params", field.name]}
          valuePropName={field.type === "boolean" ? "checked" : "value"}
          rules={[
            {
              required: field.required,
              message: `请填写参数 ${field.name}`,
            },
            {
              validator: (_, value) => {
                if (!value || field.type !== "json") {
                  return Promise.resolve();
                }
                try {
                  JSON.parse(value);
                  return Promise.resolve();
                } catch (error) {
                  return Promise.reject(new Error(`${field.name} 不是合法 JSON`));
                }
              },
            },
          ]}
        >
          {renderFieldInput(field)}
        </Form.Item>
      ))}
      <Form.Item label="执行说明" name="description">
        <Input.TextArea rows={4} placeholder="记录执行参数、预期结果或动作备注" />
      </Form.Item>
      {!selectedDeviceKey ? (
        <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="请选择目标设备后再配置动作" />
      ) : null}
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
