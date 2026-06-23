import React, { useEffect, useState } from "react";
import { Button, Card, Col, Descriptions, Empty, List, Row, Space, Typography } from "antd";
import { ArrowLeftOutlined, ReloadOutlined } from "@ant-design/icons";
import { useNavigate, useParams } from "react-router-dom";

import PageToolbar from "../components/PageToolbar";
import RunStepTimeline from "../components/RunStepTimeline";
import StatusTag from "../components/StatusTag";
import { fetchWorkflowRunDetail } from "../services/workflowApi";

const { Text } = Typography;

/**
 * 格式化事件摘要文本。
 *
 * Args:
 *     event: 运行事件。
 *
 * Returns:
 *     事件摘要文案。
 */
function formatEventSummary(event) {
  return (
    event?.message ||
    event?.summary ||
    event?.event ||
    event?.event_type ||
    event?.type ||
    "未命名事件"
  );
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
  const [detail, setDetail] = useState(null);
  const [loading, setLoading] = useState(false);
  const [loadFailed, setLoadFailed] = useState(false);
  const isSmartAccess = detail?.source === "smartaccess";

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
      setDetail(data);
      setLoadFailed(false);
    } catch (error) {
      setDetail(null);
      setLoadFailed(true);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadDetail();
  }, [runId]);

  return (
    <section className="page-section">
      <PageToolbar />
      {!detail && !loading ? (
        <Empty
          description={loadFailed ? "运行详情接口暂不可用" : "未找到对应运行记录"}
          style={{ marginBottom: 16 }}
        />
      ) : null}
      <Row gutter={[16, 16]}>
        <Col xs={24} xl={10}>
          <Card title="基础信息" loading={loading}>
            <Descriptions column={1} size="small">
              <Descriptions.Item label="运行编号">{detail?.run_id || "--"}</Descriptions.Item>
              <Descriptions.Item label="工作流名称">
                {detail?.workflow_name || "--"}
              </Descriptions.Item>
              <Descriptions.Item label="任务来源">
                {isSmartAccess ? "SmartAccess" : "SpecLabOS"}
              </Descriptions.Item>
              <Descriptions.Item label="模板">
                {detail?.template_id
                  ? `${detail.template_id}@${detail.template_version || ""}`
                  : "--"}
              </Descriptions.Item>
              <Descriptions.Item label="锚点配置">
                {detail?.anchor_profile || "--"}
              </Descriptions.Item>
              <Descriptions.Item label="当前状态">
                <StatusTag status={detail?.status} />
              </Descriptions.Item>
              <Descriptions.Item label="当前进度">
                {detail ? `${detail.current_step_index}/${detail.total_steps}` : "--"}
              </Descriptions.Item>
              <Descriptions.Item label="触发方式">
                {detail?.trigger_source || "--"}
              </Descriptions.Item>
              <Descriptions.Item label="操作人">{detail?.operator_name || "--"}</Descriptions.Item>
              <Descriptions.Item label="开始时间">{detail?.started_at || "--"}</Descriptions.Item>
              <Descriptions.Item label="结束时间">
                {detail?.finished_at || "尚未完成"}
              </Descriptions.Item>
            </Descriptions>
          </Card>
        </Col>
        <Col xs={24} xl={14}>
          <Card
            title={isSmartAccess ? "SmartAccess 步骤与 Trace" : "步骤执行时间线"}
            loading={loading}
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
          >
            <RunStepTimeline steps={detail?.steps || []} />
            {isSmartAccess ? (
              <List
                style={{ marginTop: 16 }}
                header="事件摘要"
                dataSource={detail?.events || []}
                locale={{ emptyText: "暂无事件记录" }}
                renderItem={(event) => (
                  <List.Item>
                    <Space direction="vertical" size={2} style={{ width: "100%" }}>
                      <Space wrap>
                        <Text strong>{formatEventSummary(event)}</Text>
                        <StatusTag status={event?.status || event?.level || "info"} />
                      </Space>
                      <Text type="secondary">
                        {event?.timestamp || event?.created_at || event?.time || "--"}
                      </Text>
                    </Space>
                  </List.Item>
                )}
              />
            ) : null}
          </Card>
        </Col>
      </Row>
    </section>
  );
}
