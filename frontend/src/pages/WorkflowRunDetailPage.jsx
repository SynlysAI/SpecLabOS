import React, { useEffect, useState } from "react";
import { Alert, Button, Card, Col, Descriptions, Row, Space } from "antd";
import { ArrowLeftOutlined, ReloadOutlined } from "@ant-design/icons";
import { useNavigate, useParams } from "react-router-dom";

import PageToolbar from "../components/PageToolbar";
import RunStepTimeline from "../components/RunStepTimeline";
import StatusTag from "../components/StatusTag";
import { http } from "../services/http";

const FALLBACK_RUN_DETAIL = {
  run_id: "RUN-20260427-001",
  workflow_name: "样品全流程分析",
  status: "running",
  current_step_index: 2,
  total_steps: 4,
  started_at: "2026-04-27 10:15",
  finished_at: "",
  trigger_source: "手动触发",
  operator_name: "lab-admin",
  steps: [
    {
      name: "样品预检",
      status: "online",
      started_at: "2026-04-27 10:15",
      finished_at: "2026-04-27 10:18",
      description: "完成条码和收样状态核验。"
    },
    {
      name: "仪器采集",
      status: "running",
      started_at: "2026-04-27 10:20",
      finished_at: "",
      description: "等待 LC-MS 上传原始谱图。"
    },
    {
      name: "自动分析",
      status: "idle",
      started_at: "",
      finished_at: "",
      description: "采集完成后自动进入分析。"
    }
  ]
};

/**
 * 获取运行详情。
 *
 * Args:
 *     runId: 运行编号。
 *
 * Returns:
 *     单条运行详情。
 */
async function fetchWorkflowRunDetail(runId) {
  const response = await http.get(`/api/workflow-runs/${runId}`);
  return response.data;
}

/**
 * 任务运行详情页。
 *
 * Returns:
 *     展示单次任务运行摘要与步骤详情。
 */
export default function WorkflowRunDetailPage() {
  const navigate = useNavigate();
  const { runId } = useParams();
  const [detail, setDetail] = useState(FALLBACK_RUN_DETAIL);
  const [loading, setLoading] = useState(false);
  const [usingFallbackData, setUsingFallbackData] = useState(true);

  /**
   * 加载运行详情。
   *
   * Returns:
   *     无返回值。
   */
  async function loadDetail() {
    setLoading(true);
    try {
      const data = await fetchWorkflowRunDetail(runId);
      setDetail({
        ...FALLBACK_RUN_DETAIL,
        ...data
      });
      setUsingFallbackData(false);
    } catch (error) {
      setDetail({
        ...FALLBACK_RUN_DETAIL,
        run_id: runId || FALLBACK_RUN_DETAIL.run_id
      });
      setUsingFallbackData(true);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadDetail();
  }, [runId]);

  return (
    <section className="page-section">
      <PageToolbar
        title="运行详情"
        subtitle="查看单次工作流运行状态、发起信息和各步骤执行结果。"
        extra={
          <Space>
            <Button icon={<ArrowLeftOutlined />} onClick={() => navigate("/runs")}>
              返回列表
            </Button>
            <Button icon={<ReloadOutlined />} loading={loading} onClick={loadDetail}>
              刷新详情
            </Button>
          </Space>
        }
      />
      {usingFallbackData ? (
        <Alert
          type="warning"
          showIcon
          message="运行详情接口暂不可用，当前展示示例详情。"
          style={{ marginBottom: 16 }}
        />
      ) : null}
      <Row gutter={[16, 16]}>
        <Col xs={24} xl={10}>
          <Card title="基础信息" loading={loading}>
            <Descriptions column={1} size="small">
              <Descriptions.Item label="运行编号">{detail.run_id}</Descriptions.Item>
              <Descriptions.Item label="工作流名称">{detail.workflow_name}</Descriptions.Item>
              <Descriptions.Item label="当前状态">
                <StatusTag status={detail.status} />
              </Descriptions.Item>
              <Descriptions.Item label="当前进度">
                {`${detail.current_step_index}/${detail.total_steps}`}
              </Descriptions.Item>
              <Descriptions.Item label="触发方式">{detail.trigger_source}</Descriptions.Item>
              <Descriptions.Item label="操作人">{detail.operator_name}</Descriptions.Item>
              <Descriptions.Item label="开始时间">{detail.started_at}</Descriptions.Item>
              <Descriptions.Item label="结束时间">
                {detail.finished_at || "尚未完成"}
              </Descriptions.Item>
            </Descriptions>
          </Card>
        </Col>
        <Col xs={24} xl={14}>
          <Card title="步骤执行时间线" loading={loading}>
            <RunStepTimeline steps={detail.steps} />
          </Card>
        </Col>
      </Row>
    </section>
  );
}
