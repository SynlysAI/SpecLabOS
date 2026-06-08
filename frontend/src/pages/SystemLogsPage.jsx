import React, { useEffect, useState } from "react";
import {
  Alert,
  Button,
  Card,
  Col,
  DatePicker,
  Empty,
  Form,
  Input,
  Row,
  Select,
  Space,
  Table,
  Typography
} from "antd";
import dayjs from "dayjs";

import PageToolbar from "../components/PageToolbar";
import StatusTag from "../components/StatusTag";
import { fetchAutomationRateSummary, fetchSystemLogs } from "../services/logApi";

const { Paragraph, Text } = Typography;

const LEVEL_OPTIONS = [
  { label: "全部级别", value: "all" },
  { label: "信息", value: "info" },
  { label: "告警", value: "warning" },
  { label: "错误", value: "error" }
];

const SOURCE_OPTIONS = [
  { label: "全部来源", value: "all" },
  { label: "Raman", value: "raman" },
  { label: "GPC/LCMS", value: "gpc-lcms" },
  { label: "NMR", value: "nmr" }
];

const DEFAULT_DATE = dayjs();
const FALLBACK_AUTOMATION_SUMMARY = {
  overall_rate: 0,
  metrics: [
    {
      key: "gpc",
      label: "GPC",
      rate: 0,
      sample_count: 0,
      completed_count: 0,
      source_type: "csv",
      description: "等待远程表接入。"
    },
    {
      key: "lcms",
      label: "LCMS",
      rate: 0,
      sample_count: 0,
      completed_count: 0,
      source_type: "csv",
      description: "等待远程表接入。"
    },
    {
      key: "nmr",
      label: "NMR",
      rate: 0,
      sample_count: 0,
      completed_count: 0,
      source_type: "csv",
      description: "等待远程表接入。"
    },
    {
      key: "raman",
      label: "Raman",
      rate: 0,
      sample_count: 0,
      completed_count: 0,
      source_type: "log",
      description: "等待日志统计。"
    }
  ]
};

const columns = [
  {
    title: "级别",
    dataIndex: "level",
    key: "level",
    width: 120,
    render: (value) => <StatusTag status={value} />
  },
  { title: "日志来源", dataIndex: "source_label", key: "source_label", width: 120 },
  { title: "服务模块", dataIndex: "service_name", key: "service_name", width: 180 },
  {
    title: "日志内容",
    dataIndex: "message",
    key: "message",
    render: (_, record) => (
      <div>
        <Paragraph style={{ marginBottom: 4 }}>{record.message}</Paragraph>
        {record.file_path ? (
          <Text type="secondary" style={{ fontSize: 12 }}>
            来源文件：{record.file_path}
          </Text>
        ) : null}
        {record.raw_content ? (
          <Paragraph
            type="secondary"
            ellipsis={{ rows: 2, expandable: true, symbol: "展开原始日志" }}
            style={{ marginTop: 4, marginBottom: 0, fontSize: 12 }}
          >
            原始内容：{record.raw_content}
          </Paragraph>
        ) : null}
      </div>
    )
  },
  { title: "时间", dataIndex: "created_at", key: "created_at", width: 180 }
];

/**
 * 提取接口请求失败原因。
 *
 * Args:
 *     error: 请求异常对象。
 *
 * Returns:
 *     可直接展示给用户的失败原因文本。
 */
function buildRequestErrorMessage(error) {
  const baseUrl = error?.config?.baseURL || "http://127.0.0.1:8000";
  const requestPath = error?.config?.url || "";
  const requestTarget = requestPath ? `${baseUrl}${requestPath}` : baseUrl;
  const detail = error?.response?.data?.detail;

  if (typeof detail === "string" && detail.trim()) {
    return `后端返回 ${error.response.status}：${detail}`;
  }

  if (error?.code === "ECONNABORTED") {
    return `请求 ${requestTarget} 超时，请检查后端服务状态或远程日志目录是否响应缓慢。`;
  }

  if (error?.message === "Network Error") {
    return `无法连接 ${baseUrl}，请确认后端服务已启动。`;
  }

  if (error?.response?.status) {
    return `请求 ${requestTarget} 失败，HTTP ${error.response.status}。`;
  }

  if (typeof error?.message === "string" && error.message.trim()) {
    return `请求 ${requestTarget} 失败：${error.message}`;
  }

  return `请求 ${requestTarget} 失败，请检查后端服务状态。`;
}

/**
 * 规范日志数据。
 *
 * Args:
 *     items: 原始日志列表。
 *
 * Returns:
 *     可直接供表格使用的日志列表。
 */
function normalizeLogs(items) {
  return items.map((item, index) => ({
    id: item.id || `log-${index}`,
    level: item.level || "idle",
    source: item.source || "system",
    source_label: item.source_label || item.source || "System",
    service_name: item.service_name || item.service || "unknown",
    message: item.message || "无日志内容",
    created_at: item.created_at || "--",
    file_path: item.file_path || "",
    raw_content: item.raw_content || ""
  }));
}

/**
 * 规范自动化率摘要。
 *
 * Args:
 *     summary: 原始自动化率摘要。
 *
 * Returns:
 *     适配页面展示的自动化率摘要。
 */
function normalizeAutomationSummary(summary) {
  const normalizedMetrics = (summary?.metrics || FALLBACK_AUTOMATION_SUMMARY.metrics).map((metric) => ({
    key: metric.key,
    label: metric.label,
    rate: Number(metric.rate || 0),
    sample_count: Number(metric.sample_count || 0),
    completed_count: Number(metric.completed_count || 0),
    source_type: metric.source_type || "",
    description: metric.description || ""
  }));
  return {
    overall_rate: Number(summary?.overall_rate || 0),
    metrics: normalizedMetrics
  };
}

/**
 * 格式化百分比文本。
 *
 * Args:
 *     value: 比例数值。
 *
 * Returns:
 *     百分比字符串。
 */
function formatRate(value) {
  return `${(Number(value || 0) * 100).toFixed(1)}%`;
}

/**
 * 系统日志页。
 *
 * Returns:
 *     展示自动化率摘要、日志筛选栏和日志表格。
 */
export default function SystemLogsPage() {
  const [form] = Form.useForm();
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [loadFailed, setLoadFailed] = useState(false);
  const [logsErrorMessage, setLogsErrorMessage] = useState("");
  const [summary, setSummary] = useState(FALLBACK_AUTOMATION_SUMMARY);
  const [summaryLoading, setSummaryLoading] = useState(false);
  const [summaryFailed, setSummaryFailed] = useState(false);
  const [summaryErrorMessage, setSummaryErrorMessage] = useState("");

  /**
   * 加载系统日志。
   *
   * Args:
   *     filters: 日志筛选条件。
   *
   * Returns:
   *     无返回值。
   */
  async function loadLogs(filters = form.getFieldsValue()) {
    setLoading(true);
    try {
      const normalizedFilters = {
        ...filters,
        date: filters.date && typeof filters.date === "object" && typeof filters.date.format === "function"
          ? filters.date.format("YYYY-MM-DD")
          : filters.date || DEFAULT_DATE.format("YYYY-MM-DD")
      };
      const items = await fetchSystemLogs(normalizedFilters);
      setLogs(normalizeLogs(items));
      setLoadFailed(false);
      setLogsErrorMessage("");
    } catch (error) {
      console.error("加载系统日志失败", error);
      setLogs([]);
      setLoadFailed(true);
      setLogsErrorMessage(buildRequestErrorMessage(error));
    } finally {
      setLoading(false);
    }
  }

  /**
   * 加载自动化率摘要。
   *
   * Returns:
   *     无返回值。
   */
  async function loadAutomationSummary() {
    setSummaryLoading(true);
    try {
      const response = await fetchAutomationRateSummary();
      setSummary(normalizeAutomationSummary(response));
      setSummaryFailed(false);
      setSummaryErrorMessage("");
    } catch (error) {
      console.error("加载自动化率摘要失败", error);
      setSummary(FALLBACK_AUTOMATION_SUMMARY);
      setSummaryFailed(true);
      setSummaryErrorMessage(buildRequestErrorMessage(error));
    } finally {
      setSummaryLoading(false);
    }
  }

  useEffect(() => {
    form.setFieldsValue({
      keyword: "",
      level: "all",
      source: "all",
      date: DEFAULT_DATE
    });
    loadAutomationSummary();
    loadLogs({
      keyword: "",
      level: "all",
      source: "all",
      date: DEFAULT_DATE.format("YYYY-MM-DD")
    });
  }, []);

  return (
    <section className="page-section">
      <PageToolbar />
      {summaryFailed ? (
        <Alert
          type="warning"
          showIcon
          message="自动化率接口暂不可用，当前展示占位统计。"
          description={summaryErrorMessage}
          style={{ marginBottom: 16 }}
        />
      ) : null}
      <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
        <Col xs={24} md={12} xl={8}>
          <Card className="automation-summary-card" loading={summaryLoading}>
            <Text className="automation-summary-label">总体自动化率</Text>
            <div className="automation-summary-rate">{formatRate(summary.overall_rate)}</div>
            <Text type="secondary">按 GPC、LCMS、NMR、Raman 四类指标平均计算</Text>
          </Card>
        </Col>
        {summary.metrics.map((metric) => (
          <Col xs={24} sm={12} xl={4} key={metric.key}>
            <Card className="automation-metric-card" loading={summaryLoading}>
              <Text className="automation-metric-label">{metric.label}</Text>
              <div className="automation-metric-rate">{formatRate(metric.rate)}</div>
              <Text className="automation-metric-meta">
                样本 {metric.sample_count} / 完整 {metric.completed_count}
              </Text>
              <Paragraph
                ellipsis={{ rows: 2, tooltip: metric.description }}
                type="secondary"
                style={{ marginTop: 8, marginBottom: 0, fontSize: 12 }}
              >
                {metric.description}
              </Paragraph>
            </Card>
          </Col>
        ))}
      </Row>
      <Card title="日志检索">
        <Form form={form} layout="inline" onFinish={loadLogs} style={{ marginBottom: 16 }}>
          <Form.Item name="keyword" style={{ marginBottom: 0 }}>
            <Input allowClear placeholder="关键字搜索" style={{ width: 240 }} />
          </Form.Item>
          <Form.Item name="level" style={{ marginBottom: 0 }}>
            <Select options={LEVEL_OPTIONS} style={{ width: 140 }} />
          </Form.Item>
          <Form.Item name="source" style={{ marginBottom: 0 }}>
            <Select options={SOURCE_OPTIONS} style={{ width: 160 }} />
          </Form.Item>
          <Form.Item name="date" style={{ marginBottom: 0 }}>
            <DatePicker style={{ width: 160 }} />
          </Form.Item>
          <Form.Item style={{ marginBottom: 0 }}>
            <Space>
              <Button htmlType="submit" type="primary">
                查询
              </Button>
              <Button
                onClick={() => {
                  form.resetFields();
                  form.setFieldsValue({
                    keyword: "",
                    level: "all",
                    source: "all",
                    date: DEFAULT_DATE
                  });
                  loadAutomationSummary();
                  loadLogs({
                    keyword: "",
                    level: "all",
                    source: "all",
                    date: DEFAULT_DATE.format("YYYY-MM-DD")
                  });
                }}
              >
                重置
              </Button>
            </Space>
          </Form.Item>
        </Form>
        <Table
          rowKey="id"
          columns={columns}
          dataSource={logs}
          loading={loading}
          pagination={{ pageSize: 20, showSizeChanger: false }}
          locale={{
            emptyText: loadFailed ? (
              <Empty description={logsErrorMessage || "日志接口暂不可用"} />
            ) : (
              <Empty description="暂无设备日志" />
            ),
          }}
        />
      </Card>
    </section>
  );
}
