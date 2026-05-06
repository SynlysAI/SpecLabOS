import React, { useEffect, useState } from "react";
import { Button, Col, Empty, Form, Input, InputNumber, Row, Segmented, Select, Space, Switch, Alert } from "antd";
import { LoadingOutlined } from "@ant-design/icons";
import { executeCameraFocus } from "../services/deviceApi";

const RAMAN_CAPTURE_ACTION_KEY = "raman.capture";
const RAMAN_CAMERA_FOCUS_ACTION_KEY = "raman.camera_focus";
const RAMAN_CAPTURE_CALLBACK_URL = "http://127.0.0.1:8099/raman/jy/callback";

const CAMERA_FOCUS_DEFAULTS = {
  rt: 8000,
  rb: 5000,
  s: 3,
};
const RAMAN_CAPTURE_DEFAULTS = {
  explore_time: 5,
  integer: 1,
  power_type: 2,
  laser: 20,
  grating_index: 1,
  center_wave: 724.75,
};

/**
 * 判断当前动作是否为 Raman 采集任务。
 *
 * Args:
 *     actionKey: 当前选中的动作标识。
 *
 * Returns:
 *     是否为 Raman 采集动作。
 */
function isRamanCaptureAction(actionKey) {
  return actionKey === RAMAN_CAPTURE_ACTION_KEY;
}

/**
 * 判断当前动作是否为 Raman 镜头对焦。
 *
 * Args:
 *     actionKey: 当前选中的动作标识。
 *
 * Returns:
 *     是否为镜头对焦动作。
 */
function isRamanCameraFocusAction(actionKey) {
  return actionKey === RAMAN_CAMERA_FOCUS_ACTION_KEY;
}

/**
 * 构建 Raman 采集表单的默认参数。
 *
 * Returns:
 *     Raman 采集参数默认值。
 */
function buildRamanCaptureDefaults() {
  return {
    ...RAMAN_CAPTURE_DEFAULTS,
    callback_url: RAMAN_CAPTURE_CALLBACK_URL,
  };
}

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
 * 渲染 Raman 采集任务的表单模式字段。
 *
 * Args:
 *     form: 表单实例。
 *
 * Returns:
 *     Raman 采集参数输入区域。
 */
function renderRamanCaptureFields(form) {
  return (
    <>
      <div style={{ marginBottom: 8, color: "rgba(0, 0, 0, 0.88)" }}>
        <span style={{ color: "#ff4d4f", marginRight: 4 }}>*</span>
        capture 参数输入
      </div>
      <div
        style={{
          marginBottom: 24,
          padding: 16,
          border: "1px solid #d9e2f1",
          borderRadius: 12,
          background: "#f8fbff",
        }}
      >
        <Form.Item
          name="capture_input_mode"
          initialValue="form"
          style={{ marginBottom: 16 }}
        >
          <Segmented
            block
            options={[
              { label: "表单输入", value: "form" },
              { label: "JSON 输入", value: "json" },
            ]}
          />
        </Form.Item>
      <Form.Item
        noStyle
        shouldUpdate={(previousValues, currentValues) =>
          previousValues.capture_input_mode !== currentValues.capture_input_mode
        }
      >
        {() => {
          const inputMode = form.getFieldValue("capture_input_mode") || "form";

          if (inputMode === "json") {
            return (
              <Form.Item
                label="capture"
                name={["action_params", "capture"]}
                rules={[
                  { required: true, message: "请输入 capture 的 JSON 内容" },
                  {
                    validator: (_, value) => {
                      if (!value) {
                        return Promise.resolve();
                      }
                      try {
                        JSON.parse(value);
                        return Promise.resolve();
                      } catch (error) {
                        return Promise.reject(new Error("capture 不是合法 JSON"));
                      }
                    },
                  },
                ]}
              >
                <Input.TextArea
                  rows={8}
                  placeholder="请输入 capture 的 JSON 内容"
                />
              </Form.Item>
            );
          }

          return (
            <>
              <Row gutter={[16, 0]}>
                <Col xs={24} md={12}>
                  <Form.Item
                    label="explore_time"
                    name={["capture_form", "explore_time"]}
                    initialValue={RAMAN_CAPTURE_DEFAULTS.explore_time}
                    rules={[{ required: true, message: "请输入 explore_time" }]}
                  >
                    <InputNumber style={{ width: "100%" }} />
                  </Form.Item>
                </Col>
                <Col xs={24} md={12}>
                  <Form.Item
                    label="integer"
                    name={["capture_form", "integer"]}
                    initialValue={RAMAN_CAPTURE_DEFAULTS.integer}
                    rules={[{ required: true, message: "请输入 integer" }]}
                  >
                    <InputNumber style={{ width: "100%" }} />
                  </Form.Item>
                </Col>
                <Col xs={24} md={12}>
                  <Form.Item
                    label="power_type"
                    name={["capture_form", "power_type"]}
                    initialValue={RAMAN_CAPTURE_DEFAULTS.power_type}
                    rules={[{ required: true, message: "请输入 power_type" }]}
                  >
                    <InputNumber style={{ width: "100%" }} />
                  </Form.Item>
                </Col>
                <Col xs={24} md={12}>
                  <Form.Item
                    label="laser"
                    name={["capture_form", "laser"]}
                    initialValue={RAMAN_CAPTURE_DEFAULTS.laser}
                    rules={[{ required: true, message: "请输入 laser" }]}
                  >
                    <InputNumber style={{ width: "100%" }} />
                  </Form.Item>
                </Col>
                <Col xs={24} md={12}>
                  <Form.Item
                    label="grating_index"
                    name={["capture_form", "grating_index"]}
                    initialValue={RAMAN_CAPTURE_DEFAULTS.grating_index}
                    rules={[{ required: true, message: "请输入 grating_index" }]}
                  >
                    <InputNumber style={{ width: "100%" }} />
                  </Form.Item>
                </Col>
                <Col xs={24} md={12}>
                  <Form.Item
                    label="center_wave"
                    name={["capture_form", "center_wave"]}
                    initialValue={RAMAN_CAPTURE_DEFAULTS.center_wave}
                    rules={[{ required: true, message: "请输入 center_wave" }]}
                  >
                    <InputNumber style={{ width: "100%" }} />
                  </Form.Item>
                </Col>
                <Col span={24}>
                  <Form.Item
                    label="callback_url"
                    name={["capture_form", "callback_url"]}
                    initialValue={RAMAN_CAPTURE_CALLBACK_URL}
                    style={{ marginBottom: 0 }}
                  >
                    <Input disabled />
                  </Form.Item>
                </Col>
              </Row>
            </>
          );
        }}
      </Form.Item>
      </div>
    </>
  );
}

/**
 * Raman 镜头对焦表单组件。
 *
 * Args:
 *     form: 表单实例。
 *     selectedDeviceKey: 当前选中的设备标识。
 *
 * Returns:
 *     镜头对焦参数输入区域。
 */
function RamanCameraFocusFields({ form, selectedDeviceKey }) {
  const [focusing, setFocusing] = useState(false);
  const [focusResult, setFocusResult] = useState(null);

  /**
   * 执行镜头对焦操作。
   */
  async function handleStartFocus() {
    const values = form.getFieldsValue();
    const focusForm = values.focus_form || {};
    const params = {
      rt: focusForm.rt ?? CAMERA_FOCUS_DEFAULTS.rt,
      rb: focusForm.rb ?? CAMERA_FOCUS_DEFAULTS.rb,
      s: focusForm.s ?? CAMERA_FOCUS_DEFAULTS.s,
    };

    setFocusing(true);
    setFocusResult(null);
    try {
      const result = await executeCameraFocus(selectedDeviceKey, params);
      setFocusResult(result);
    } catch (error) {
      setFocusResult({
        code: -1,
        msg: error?.response?.data?.detail || error.message || "对焦请求失败",
      });
    } finally {
      setFocusing(false);
    }
  }

  return (
    <>
      <div style={{ marginBottom: 8, color: "rgba(0, 0, 0, 0.88)" }}>
        <span style={{ color: "#ff4d4f", marginRight: 4 }}>*</span>
        对焦参数配置
      </div>
      <div
        style={{
          marginBottom: 24,
          padding: 16,
          border: "1px solid #d9e2f1",
          borderRadius: 12,
          background: "#f8fbff",
        }}
      >
        <Row gutter={[16, 0]}>
          <Col xs={24} md={8}>
            <Form.Item
              label="上限 (rt)"
              name={["focus_form", "rt"]}
              initialValue={CAMERA_FOCUS_DEFAULTS.rt}
              rules={[{ required: true, message: "请输入上限" }]}
            >
              <InputNumber style={{ width: "100%" }} min={1} />
            </Form.Item>
          </Col>
          <Col xs={24} md={8}>
            <Form.Item
              label="下限 (rb)"
              name={["focus_form", "rb"]}
              initialValue={CAMERA_FOCUS_DEFAULTS.rb}
              rules={[{ required: true, message: "请输入下限" }]}
            >
              <InputNumber style={{ width: "100%" }} min={1} />
            </Form.Item>
          </Col>
          <Col xs={24} md={8}>
            <Form.Item
              label="步长 (s)"
              name={["focus_form", "s"]}
              initialValue={CAMERA_FOCUS_DEFAULTS.s}
              rules={[{ required: true, message: "请输入步长" }]}
            >
              <InputNumber style={{ width: "100%" }} min={1} />
            </Form.Item>
          </Col>
        </Row>
        <Button
          type="primary"
          icon={focusing ? <LoadingOutlined /> : null}
          disabled={focusing || !selectedDeviceKey}
          onClick={handleStartFocus}
          style={{ marginBottom: focusResult ? 12 : 0 }}
        >
          {focusing ? "对焦中..." : "开始对焦"}
        </Button>
        {focusResult && (
          <Alert
            type={focusResult.code === 0 ? "success" : "error"}
            message={focusResult.msg}
            showIcon
            style={{ marginTop: 12 }}
          />
        )}
      </div>
    </>
  );
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
  const isRamanCapture = isRamanCaptureAction(selectedActionKey);
  const isCameraFocus = isRamanCameraFocusAction(selectedActionKey);

  /**
   * 处理步骤表单提交。
   *
   * Args:
   *     values: 原始表单值。
   *
   * Returns:
   *     无返回值。
   */
  function handleFinish(values) {
    if (!isRamanCapture && !isCameraFocus) {
      onSubmit(values);
      return;
    }

    if (isCameraFocus) {
      const focusForm = values.focus_form || {};
      onSubmit({
        ...values,
        action_params: {
          rt: focusForm.rt ?? CAMERA_FOCUS_DEFAULTS.rt,
          rb: focusForm.rb ?? CAMERA_FOCUS_DEFAULTS.rb,
          s: focusForm.s ?? CAMERA_FOCUS_DEFAULTS.s,
        },
      });
      return;
    }

    const inputMode = values.capture_input_mode || "form";
    const nextValues = {
      ...values,
      action_params: {
        ...(values.action_params || {}),
      },
    };

    if (inputMode === "form") {
      nextValues.action_params.capture = {
        ...buildRamanCaptureDefaults(),
        ...(values.capture_form || {}),
        callback_url: RAMAN_CAPTURE_CALLBACK_URL,
      };
    }

    onSubmit(nextValues);
  }

  useEffect(() => {
    if (!isRamanCapture && !isCameraFocus) {
      form.setFieldValue("capture_input_mode", undefined);
      form.setFieldValue("capture_form", undefined);
      form.setFieldValue("focus_form", undefined);
      return;
    }

    if (isRamanCapture) {
      form.setFieldValue("capture_input_mode", "form");
      form.setFieldValue("capture_form", buildRamanCaptureDefaults());
      form.setFieldValue(["action_params", "capture"], undefined);
    }

    if (isCameraFocus) {
      form.setFieldValue("focus_form", { ...CAMERA_FOCUS_DEFAULTS });
    }
  }, [form, isRamanCapture, isCameraFocus, selectedActionKey]);

  return (
    <Form form={form} layout="vertical" onFinish={handleFinish}>
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
      {isCameraFocus && <RamanCameraFocusFields form={form} selectedDeviceKey={selectedDeviceKey} />}
      {!isCameraFocus && currentSchema.map((field) => {
        if (isRamanCapture && field.name === "capture") {
          return <React.Fragment key={field.name}>{renderRamanCaptureFields(form)}</React.Fragment>;
        }

        return (
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
        );
      })}
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
