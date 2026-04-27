import React, { useState } from "react";
import { Button, Card, Col, Form, Row, Space, message } from "antd";

import PageToolbar from "../components/PageToolbar";
import WorkflowStepForm from "../components/WorkflowStepForm";
import WorkflowStepList from "../components/WorkflowStepList";
import { createWorkflow } from "../services/workflowApi";

const STEP_TYPE_LABELS = {
  collect: "采集",
  analyze: "分析",
  export: "导出"
};

/**
 * 工作流编排页。
 *
 * Returns:
 *     提供左侧步骤配置和右侧步骤列表的编排界面。
 */
export default function WorkflowBuilderPage() {
  const [form] = Form.useForm();
  const [steps, setSteps] = useState([
    {
      key: "step-seed-1",
      name: "样品预检",
      type: "collect",
      typeLabel: "采集",
      description: "确认样品编号、条码和接收状态。"
    }
  ]);
  const [submitting, setSubmitting] = useState(false);
  const [messageApi, contextHolder] = message.useMessage();

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
    setSteps((currentSteps) => [
      ...currentSteps,
      {
        key: `step-${Date.now()}`,
        ...values,
        typeLabel: STEP_TYPE_LABELS[values.type] || values.type
      }
    ]);
    form.resetFields();
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
        name: "新建工作流草稿",
        steps: steps.map((item, index) => ({
          order: index + 1,
          name: item.name,
          type: item.type,
          description: item.description
        }))
      });
      messageApi.success("工作流草稿提交成功");
    } catch (error) {
      messageApi.info("接口未就绪，已保留本地编排结果");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <section className="page-section">
      {contextHolder}
      <PageToolbar
        title="工作流编排"
        subtitle="左侧配置步骤内容，右侧维护顺序列表。"
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
      <Row gutter={[16, 16]}>
        <Col xs={24} xl={10}>
          <Card title="步骤配置" bordered={false}>
            <WorkflowStepForm form={form} onSubmit={handleAddStep} />
          </Card>
        </Col>
        <Col xs={24} xl={14}>
          <Card title="当前工作流步骤" bordered={false}>
            <WorkflowStepList steps={steps} onRemove={handleRemoveStep} />
          </Card>
        </Col>
      </Row>
    </section>
  );
}
