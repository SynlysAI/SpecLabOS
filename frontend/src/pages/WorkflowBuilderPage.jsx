import React, { useEffect, useMemo, useState } from "react";
import { Alert, Button, Card, Col, Empty, Form, Row, Space, message } from "antd";

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
  const [steps, setSteps] = useState([]);
  const [devices, setDevices] = useState([]);
  const [actionOptions, setActionOptions] = useState([]);
  const [selectedDeviceKey, setSelectedDeviceKey] = useState("");
  const [workflows, setWorkflows] = useState([]);
  const [submitting, setSubmitting] = useState(false);
  const [loadingDevices, setLoadingDevices] = useState(false);
  const [loadingActions, setLoadingActions] = useState(false);
  const [messageApi, contextHolder] = message.useMessage();
  const [usingActionFallback, setUsingActionFallback] = useState(false);
  const [loadFailed, setLoadFailed] = useState(false);

  const deviceOptions = useMemo(
    () =>
      devices.map((device) => ({
        label: `${device.name} · ${device.device_type}`,
        value: device.key
      })),
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
   * 添加工作流步骤。
   *
   * Args:
   *     values: 步骤表单值。
   *
   * Returns:
   *     无返回值。
   */
  function handleAddStep(values) {
    const selectedAction = actionOptions.find((item) => item.value === values.action_key);
    setSteps((currentSteps) => [
      ...currentSteps,
      {
        key: `step-${Date.now()}`,
        name: values.name,
        actionKey: values.action_key,
        deviceKey: values.device_key,
        typeLabel: selectedAction?.label || values.action_key,
        description: values.description
      }
    ]);
    form.resetFields();
    setSelectedDeviceKey("");
    setActionOptions([]);
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
    setSubmitting(true);
    try {
      await createWorkflow({
        name: `workflow_${Date.now()}`,
        steps: steps.map((item, index) => ({
          step_id: item.key,
          device_key: item.deviceKey,
          action_key: item.actionKey,
          display_name: item.name,
          params: {
            description: item.description,
            order: index + 1,
          },
          confirm_params: {},
        }))
      });
      messageApi.success("工作流已创建并生成运行记录");
      setSteps([]);
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
      setUsingActionFallback(false);
    } catch (error) {
      setActionOptions([]);
      setUsingActionFallback(true);
      messageApi.error("设备动作目录接口不可用");
    } finally {
      setLoadingActions(false);
    }
  }

  return (
    <section className="page-section">
      {contextHolder}
      <PageToolbar
        title="工作流编排"
        subtitle="基于真实设备实例和设备动作目录编排顺序工作流。"
        extra={
          <Space>
            <Button onClick={() => form.resetFields()}>重置表单</Button>
            <Button
              type="primary"
              onClick={handleSubmitWorkflow}
              loading={submitting}
              disabled={!steps.length}
            >
              保存草稿
            </Button>
          </Space>
        }
      />
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
        <Col xs={24} xl={10}>
          <Card title="步骤配置" bordered={false}>
            {devices.length ? (
              <WorkflowStepForm
                form={form}
                onSubmit={handleAddStep}
                deviceOptions={deviceOptions}
                actionOptions={actionOptions}
                selectedDeviceKey={selectedDeviceKey}
                onDeviceChange={handleDeviceChange}
                loadingDevices={loadingDevices}
                loadingActions={loadingActions}
              />
            ) : (
              <Empty description="当前没有可用设备目录" />
            )}
          </Card>
        </Col>
        <Col xs={24} xl={14}>
          <Card
            title={`当前工作流步骤${workflows.length ? ` · 已保存 ${workflows.length} 条定义` : ""}`}
            bordered={false}
          >
            <WorkflowStepList steps={steps} onRemove={handleRemoveStep} />
          </Card>
        </Col>
      </Row>
    </section>
  );
}
