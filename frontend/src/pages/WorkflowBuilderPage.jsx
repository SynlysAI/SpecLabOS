import React, { useEffect, useMemo, useState } from "react";
import { Alert, Button, Card, Col, Empty, Form, Input, Row, Select, Space, Typography, message } from "antd";

import PageToolbar from "../components/PageToolbar";
import WorkflowStepForm from "../components/WorkflowStepForm";
import WorkflowStepList from "../components/WorkflowStepList";
import { fetchDevices } from "../services/deviceApi";
import {
  createWorkflow,
  fetchDeviceActions,
  fetchWorkflowDrafts,
  normalizeWorkflowDrafts,
} from "../services/workflowApi";

/**
 * 工作流编排页。
 *
 * Returns:
 *     提供左侧步骤配置和右侧步骤列表的编排界面。
 */
export default function WorkflowBuilderPage() {
  const [form] = Form.useForm();
  const [workflowForm] = Form.useForm();
  const [steps, setSteps] = useState([]);
  const [devices, setDevices] = useState([]);
  const [actionOptions, setActionOptions] = useState([]);
  const [actionSchemas, setActionSchemas] = useState({});
  const [selectedDeviceKey, setSelectedDeviceKey] = useState("");
  const [workflows, setWorkflows] = useState([]);
  const [submitting, setSubmitting] = useState(false);
  const [loadingDevices, setLoadingDevices] = useState(false);
  const [loadingActions, setLoadingActions] = useState(false);
  const [messageApi, contextHolder] = message.useMessage();
  const [usingActionFallback, setUsingActionFallback] = useState(false);
  const [loadFailed, setLoadFailed] = useState(false);
  const { Text } = Typography;

  const deviceOptions = useMemo(
    () =>
      devices.map((device) => {
        const permission = device.permission || "read";
        const hasControl = permission === "control";
        return {
          label: hasControl
            ? `${device.name} · ${device.device_type}`
            : `${device.name} · ${device.device_type}(只读,无控制权限)`,
          value: device.key,
          disabled: !hasControl,
        };
      }),
    [devices]
  );

  useEffect(() => {
    async function loadDevices() {
      setLoadingDevices(true);
      try {
        const items = await fetchDevices();
        setDevices(items);
        setLoadFailed(false);
      } catch (error) {
        setDevices([]);
        setLoadFailed(true);
        messageApi.error("设备目录接口不可用，暂时无法编排真实动作。");
      } finally {
        setLoadingDevices(false);
      }
    }

    loadDevices();
  }, []);

  useEffect(() => {
    async function loadWorkflowDrafts() {
      try {
        const items = await fetchWorkflowDrafts();
        setWorkflows(normalizeWorkflowDrafts(items));
      } catch (error) {
        setWorkflows([]);
      }
    }
    loadWorkflowDrafts();
  }, []);

  /**
   * 根据动作选项生成步骤显示名称。
   *
   * Args:
   *     actionKey: 设备动作唯一标识。
   *     options: 当前设备动作选项列表。
   *
   * Returns:
   *     优先返回设备动作名称，不存在时返回动作标识。
   */
  function buildStepName(actionKey, options) {
    const selectedAction = options.find((item) => item.value === actionKey);
    return selectedAction?.label || actionKey;
  }

  /**
   * 添加工作流步骤。
   *
   * Args:
   *     values: 步骤表单值。
   *
   * Returns:
   *     无返回值。
   */
  function handleAddStep(values) {
    const stepName = buildStepName(values.action_key, actionOptions);
    const selectedSchema = actionSchemas[values.action_key] || [];
    const rawParams = values.action_params || {};
    const normalizedParams = selectedSchema.reduce((result, field) => {
      const rawValue = rawParams[field.name];
      if (rawValue === undefined || rawValue === "") {
        return result;
      }
      if (field.type === "json") {
        result[field.name] = typeof rawValue === "string" ? JSON.parse(rawValue) : rawValue;
        return result;
      }
      result[field.name] = rawValue;
      return result;
    }, {});

    setSteps((currentSteps) => [
      ...currentSteps,
      {
        key: `step-${Date.now()}`,
        name: stepName,
        actionKey: values.action_key,
        deviceKey: selectedDeviceKey,
        typeLabel: stepName,
        description: values.description,
        params: normalizedParams,
        paramsSummary:
          Object.keys(normalizedParams).length > 0
            ? `参数: ${JSON.stringify(normalizedParams)}`
            : "",
      }
    ]);
  }

  /**
   * 删除工作流步骤。
   *
   * Args:
   *     stepKey: 需要删除的步骤键。
   *
   * Returns:
   *     无返回值。
   */
  function handleRemoveStep(stepKey) {
    setSteps((currentSteps) => currentSteps.filter((item) => item.key !== stepKey));
  }

  /**
   * 保存工作流草稿。
   *
   * Returns:
   *     无返回值。
   */
  async function handleSubmitWorkflow() {
    const workflowValues = await workflowForm.validateFields();
    setSubmitting(true);
    try {
      await createWorkflow({
        name: workflowValues.name,
        created_by: workflowValues.created_by,
        device_key: selectedDeviceKey,
        steps: steps.map((item, index) => ({
          step_id: item.key,
          device_key: item.deviceKey,
          action_key: item.actionKey,
          display_name: item.name,
          params: {
            ...item.params,
            description: item.description,
            order: index + 1,
          },
          confirm_params: {},
        }))
      });
      messageApi.success("工作流已提交，正在排队执行");
      setSteps([]);
      form.resetFields();
      workflowForm.resetFields(["name"]);
      const items = await fetchWorkflowDrafts();
      setWorkflows(normalizeWorkflowDrafts(items));
    } catch (error) {
      messageApi.error("工作流提交失败，请检查后端接口状态");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleDeviceChange(deviceKey) {
    form.setFieldValue("action_key", undefined);
    form.setFieldValue("action_params", {});
    setSelectedDeviceKey(deviceKey);
    setLoadingActions(true);
    try {
      const items = await fetchDeviceActions(deviceKey);
      setActionOptions(
        items.map((item) => ({
          label: item.name,
          value: item.action_key,
        }))
      );
      setActionSchemas(
        items.reduce((result, item) => {
          result[item.action_key] = item.parameter_schema || [];
          return result;
        }, {})
      );
      setUsingActionFallback(false);
    } catch (error) {
      setActionOptions([]);
      setActionSchemas({});
      setUsingActionFallback(true);
      messageApi.error("设备动作目录接口不可用");
    } finally {
      setLoadingActions(false);
    }
  }

  return (
    <section className="page-section">
      {contextHolder}
      <PageToolbar />
      <Text type="secondary" style={{ display: "block", marginBottom: 16 }}>
        面向 SpecLabOS 本地注册设备，编排 LocalAdapter 可执行工作流。
      </Text>
      {usingActionFallback ? (
        <Alert
          type="warning"
          showIcon
          message="设备动作目录暂不可用，请先确认后端设备动作接口已启动。"
          style={{ marginBottom: 16 }}
        />
      ) : null}
      {loadFailed ? (
        <Alert
          type="warning"
          showIcon
          message="设备目录接口暂不可用，当前无法配置真实工作流步骤。"
          style={{ marginBottom: 16 }}
        />
      ) : null}
      <Row gutter={[16, 16]}>
        <Col span={24}>
          <Card title="工作流信息" bordered={false}>
            <Form form={workflowForm} layout="vertical" initialValues={{ created_by: "system" }}>
              <Row gutter={[16, 0]}>
                <Col xs={24} md={8}>
                  <Form.Item
                    label="目标设备"
                    name="device_key"
                    rules={[{ required: true, message: "请选择目标设备" }]}
                    style={{ marginBottom: 12 }}
                  >
                    <Select
                      options={deviceOptions}
                      placeholder="选择设备实例"
                      onChange={handleDeviceChange}
                      loading={loadingDevices}
                    />
                  </Form.Item>
                </Col>
                <Col xs={24} md={8}>
                  <Form.Item
                    label="工作流名称"
                    name="name"
                    rules={[{ required: true, message: "请输入工作流名称" }]}
                    style={{ marginBottom: 12 }}
                  >
                    <Input placeholder="例如：Raman 连续采集流程" />
                  </Form.Item>
                </Col>
                <Col xs={24} md={8}>
                  <Form.Item
                    label="创建人"
                    name="created_by"
                    rules={[{ required: true, message: "请输入创建人" }]}
                    style={{ marginBottom: 12 }}
                  >
                    <Input placeholder="例如：admin" />
                  </Form.Item>
                </Col>
              </Row>
            </Form>
          </Card>
        </Col>
        <Col xs={24} xl={10}>
          <Card title="步骤配置" bordered={false}>
            {devices.length ? (
              <WorkflowStepForm
                form={form}
                onSubmit={handleAddStep}
                actionOptions={actionOptions}
                actionSchemas={actionSchemas}
                selectedDeviceKey={selectedDeviceKey}
              />
            ) : (
              <Empty description="当前没有可用设备目录" />
            )}
          </Card>
        </Col>
        <Col xs={24} xl={14}>
          <Card
            title="当前工作流步骤"
            extra={
              <Space>
                <Button
                  onClick={() => {
                    setSteps([]);
                  }}
                >
                  重置表单
                </Button>
                <Button
                  type="primary"
                  onClick={handleSubmitWorkflow}
                  loading={submitting}
                  disabled={!steps.length || !selectedDeviceKey}
                >
                  提交运行
                </Button>
              </Space>
            }
            bordered={false}
          >
            <WorkflowStepList steps={steps} onRemove={handleRemoveStep} />
          </Card>
        </Col>
      </Row>
    </section>
  );
}
