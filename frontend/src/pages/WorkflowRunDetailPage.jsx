import React, { useEffect, useState } from "react";
import { Button, Card, Col, Descriptions, Drawer, Empty, List, message, Modal, Row, Space, Table, Tag, Tooltip, Typography } from "antd";
import {
  ArrowLeftOutlined,
  DisconnectOutlined,
  LinkOutlined,
  ProfileOutlined,
  ReloadOutlined,
} from "@ant-design/icons";
import { useNavigate, useParams } from "react-router-dom";

import PageToolbar from "../components/PageToolbar";
import RunStepTimeline from "../components/RunStepTimeline";
import StatusTag from "../components/StatusTag";
import { formatDateTime } from "../utils/datetime";
import {
  bindSmartAccessDataFile,
  unbindSmartAccessDataFile,
} from "../services/smartaccessApi";
import { fetchWorkflowRunDetail } from "../services/workflowApi";

const { Text } = Typography;

/**
 * 格式化文件大小展示文本。
 *
 * Args:
 *     size: 文件字节数。
 *
 * Returns:
 *     可读的大小文本。
 */
function formatFileSize(size) {
  const value = Number(size) || 0;
  if (value >= 1024 * 1024) {
    return `${(value / 1024 / 1024).toFixed(1)} MB`;
  }
  if (value >= 1024) {
    return `${(value / 1024).toFixed(1)} KB`;
  }
  return `${value} B`;
}

/**
 * 构建数据文件表格列。
 *
 * Args:
 *     onBind: 建议关联条目的确认绑定回调；为空时不渲染操作列。
 *     onUnbind: 已绑定条目的取消关联回调；为空时不渲染操作列。
 *
 * Returns:
 *     antd Table 列配置数组。
 */
function buildDataFileColumns(onBind, onUnbind) {
  const columns = [
    {
      title: "文件名",
      dataIndex: "filename",
      key: "filename",
      ellipsis: true,
      render: (value, record) => (
        <Tooltip title={record.relative_path || value || ""}>
          {value || "--"}
        </Tooltip>
      ),
    },
    {
      title: "类型",
      dataIndex: "data_type",
      key: "data_type",
      width: 100,
      ellipsis: true,
      render: (value) => value || "--",
    },
    {
      title: "大小",
      dataIndex: "file_size",
      key: "file_size",
      width: 90,
      render: (value) => formatFileSize(value),
    },
    {
      title: "入库时间",
      dataIndex: "ingested_at",
      key: "ingested_at",
      width: 170,
      render: (value) => formatDateTime(value),
    },
  ];
  if (onBind) {
    columns.push({
      title: "操作",
      key: "actions",
      width: 100,
      render: (_, record) => (
        <Button
          type="link"
          size="small"
          icon={<LinkOutlined />}
          onClick={() => onBind(record)}
        >
          关联
        </Button>
      ),
    });
  }
  if (onUnbind) {
    columns.push({
      title: "操作",
      key: "actions",
      width: 100,
      render: (_, record) => (
        <Button
          type="link"
          size="small"
          danger
          icon={<DisconnectOutlined />}
          onClick={() => onUnbind(record)}
        >
          取消关联
        </Button>
      ),
    });
  }
  return columns;
}

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
  const [eventsDrawerOpen, setEventsDrawerOpen] = useState(false);
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

  /**
   * 确认把建议关联的数据文件绑定到当前运行。
   *
   * Args:
   *     record: 数据文件记录。
   */
  async function handleBindFile(record) {
    try {
      await bindSmartAccessDataFile(runId, record.file_id);
      message.success(`已关联数据文件：${record.filename}`);
      await loadDetail();
    } catch (error) {
      message.error("数据文件关联失败，请稍后重试");
    }
  }

  /**
   * 解除数据文件与当前运行的绑定。
   *
   * Args:
   *     record: 数据文件记录。
   */
  async function handleUnbindFile(record) {
    try {
      await unbindSmartAccessDataFile(runId, record.file_id);
      message.success(`已取消关联：${record.filename}`);
      await loadDetail();
    } catch (error) {
      message.error("取消关联失败，请稍后重试");
    }
  }

  return (
    <section className="page-section">
      <PageToolbar />
      {!detail && !loading ? (
        <Empty
          description={loadFailed ? "运行详情接口暂不可用" : "未找到对应运行记录"}
          style={{ marginBottom: 16 }}
        />
      ) : null}
      <Row gutter={[16, 16]} align="stretch">
        <Col xs={24} xl={10}>
          <Card title="基础信息" loading={loading} style={{ height: "100%" }}>
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
            style={{ height: "100%" }}
            styles={{ body: { maxHeight: 420, overflowY: "auto" } }}
            extra={
              <Space>
                {isSmartAccess ? (
                  <Button
                    icon={<ProfileOutlined />}
                    onClick={() => setEventsDrawerOpen(true)}
                  >
                    事件摘要
                  </Button>
                ) : null}
                <Button
                  icon={<ArrowLeftOutlined />}
                  onClick={() =>
                    navigate(isSmartAccess ? "/tasks/smartaccess-runs" : "/tasks/orchestration-runs")
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
          </Card>
        </Col>
      </Row>
      {isSmartAccess ? (
        <Card
          title="数据结果"
          style={{ marginTop: 16 }}
          loading={loading}
          extra={
            <Space>
              <Tag bordered={false}>已绑定 {(detail?.data_files || []).length}</Tag>
              <Tag bordered={false}>建议关联 {(detail?.data_suggestions || []).length}</Tag>
            </Space>
          }
        >
          <Text strong style={{ display: "block", marginBottom: 8 }}>
            已绑定
          </Text>
          <Table
            size="small"
            rowKey="file_id"
            tableLayout="fixed"
            columns={buildDataFileColumns(null, handleUnbindFile)}
            dataSource={detail?.data_files || []}
            pagination={false}
            locale={{ emptyText: <Empty description="暂无已绑定的数据文件" image={Empty.PRESENTED_IMAGE_SIMPLE} /> }}
          />
          <Text strong style={{ display: "block", margin: "16px 0 8px" }}>
            建议关联
          </Text>
          <Table
            size="small"
            rowKey="file_id"
            tableLayout="fixed"
            columns={buildDataFileColumns(handleBindFile)}
            dataSource={detail?.data_suggestions || []}
            pagination={false}
            locale={{
              emptyText: (
                <Empty
                  description="任务时间窗内该设备新增的未绑定文件，确认后归入本次任务"
                  image={Empty.PRESENTED_IMAGE_SIMPLE}
                />
              ),
            }}
          />
        </Card>
      ) : null}
      <Drawer
        title="事件摘要"
        placement="right"
        width={560}
        open={eventsDrawerOpen}
        onClose={() => setEventsDrawerOpen(false)}
      >
        <List
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
      </Drawer>
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
