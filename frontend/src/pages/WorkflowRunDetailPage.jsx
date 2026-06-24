import React, { useEffect, useState } from "react";
import { Button, Card, Col, Descriptions, Empty, List, Modal, Row, Space, Typography } from "antd";
import { ArrowLeftOutlined, ReloadOutlined } from "@ant-design/icons";
import { useNavigate, useParams } from "react-router-dom";

import PageToolbar from "../components/PageToolbar";
import RunStepTimeline from "../components/RunStepTimeline";
import StatusTag from "../components/StatusTag";
import { fetchWorkflowRunDetail } from "../services/workflowApi";

const { Text } = Typography;

/**
 * SmartAccess 事件类型到中文标签的映射。
 */
const SMARTACCESS_EVENT_LABELS = {
  "run.accepted": "任务已接受",
  "run.rejected": "任务被拒绝",
  "run.started": "运行开始",
  "run.blocked": "运行阻塞",
  "run.recovered": "运行恢复",
  "run.completed": "运行完成",
  "run.failed": "运行失败",
  "run.cancelled": "运行取消",
  "step.started": "步骤开始",
  "step.updated": "步骤观察",
  "step.completed": "步骤完成",
};

/**
 * 解析事件中文标签。
 *
 * Args:
 *     event: 运行事件。
 *
 * Returns:
 *     事件中文标签，未识别时回退到事件类型原文。
 */
function formatEventLabel(event) {
  const eventType = event?.event_type || event?.type || "";
  return SMARTACCESS_EVENT_LABELS[eventType] || eventType || "未命名事件";
}

/**
 * 根据事件 step_index 在步骤列表中查找步骤名。
 *
 * Args:
 *     event: 运行事件。
 *     steps: 步骤详情列表。
 *
 * Returns:
 *     匹配到的步骤名；无法匹配时返回空串。
 */
function resolveStepName(event, steps) {
  const stepIndex = event?.step_index;
  if (stepIndex === undefined || stepIndex === null || !Array.isArray(steps)) {
    return "";
  }
  const step = steps[Number(stepIndex)];
  return step?.name || "";
}

/**
 * 提取事件发生的本地时间文本。
 *
 * Args:
 *     event: 运行事件。
 *
 * Returns:
 *     时间文本，无法识别时返回 "--"。
 */
function formatEventTime(event) {
  const raw = event?.timestamp || event?.created_at || event?.time || "";
  if (!raw) return "--";
  try {
    const date = new Date(raw);
    if (Number.isNaN(date.getTime())) return raw;
    return date.toLocaleString("zh-CN", { hour12: false });
  } catch {
    return raw;
  }
}

/**
 * 将事件数据格式化为 JSON 文本。
 *
 * Args:
 *     value: 事件数据。
 *
 * Returns:
 *     格式化后的展示文本。
 */
function formatEventJson(value) {
  if (value === undefined || value === null) {
    return "暂无事件数据";
  }
  try {
    return JSON.stringify(value, null, 2);
  } catch {
    return String(value);
  }
}

/**
 * 提取事件附加摘要：OCR 观察、错误信息或 detail 文本。
 *
 * Args:
 *     event: 运行事件。
 *
 * Returns:
 *     附加摘要文本，无内容时返回空串。
 */
function formatEventDetail(event) {
  const payload = event?.payload || {};
  const trace = payload?.trace || {};
  const eventType = event?.event_type || "";
  if (eventType === "step.updated" && (trace.expected_text !== undefined || trace.actual_text !== undefined)) {
    const rule = `${trace.match_mode || "contains"} ${trace.expected_text ?? ""}`.trim();
    return [
      rule ? `OCR规则: ${rule}` : "",
      `OCR实际: ${trace.actual_text ?? ""}`,
      `匹配: ${trace.matched}`,
      trace.attempts !== undefined ? `尝试: ${trace.attempts}` : "",
    ].filter(Boolean).join(" / ");
  }
  const error = payload?.error || trace?.error || "";
  if (error) return `错误：${error}`;
  const detail = payload?.detail || trace?.detail || "";
  return detail ? String(detail) : "";
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
  const [selectedEvent, setSelectedEvent] = useState(null);
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
              <Descriptions.Item label="SmartAccess 执行端">
                {detail?.smartaccess_node_id || "--"}
              </Descriptions.Item>
              <Descriptions.Item label="目标设备/软件">
                {detail?.target_device_id || "--"}
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
                <Button
                  icon={<ArrowLeftOutlined />}
                  onClick={() =>
                    navigate(isSmartAccess ? "/smartaccess/runs" : "/runs")
                  }
                >
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
                renderItem={(event) => {
                  const stepName = resolveStepName(event, detail?.steps);
                  const detailText = formatEventDetail(event);
                  return (
                    <List.Item>
                      <Space direction="vertical" size={4} style={{ width: "100%" }}>
                        <Space style={{ justifyContent: "space-between", width: "100%" }} wrap>
                          <Space wrap>
                            <StatusTag status={event?.status || event?.level || "info"} />
                            <Text strong>
                              {stepName ? `${stepName} · ` : ""}{formatEventLabel(event)}
                            </Text>
                          </Space>
                          <Button
                            type="link"
                            size="small"
                            onClick={() => setSelectedEvent(event)}
                          >
                            查看数据
                          </Button>
                        </Space>
                        <Text type="secondary">{formatEventTime(event)}</Text>
                        {detailText ? (
                          <Text
                            type={event?.status === "failed" ? "danger" : "secondary"}
                            style={{ fontSize: 12, wordBreak: "break-all" }}
                          >
                            {detailText}
                          </Text>
                        ) : null}
                      </Space>
                    </List.Item>
                  );
                }}
              />
            ) : null}
          </Card>
        </Col>
      </Row>
      <Modal
        title="事件数据"
        open={Boolean(selectedEvent)}
        footer={null}
        onCancel={() => setSelectedEvent(null)}
        width={760}
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
          {formatEventJson(selectedEvent)}
        </pre>
      </Modal>
    </section>
  );
}
