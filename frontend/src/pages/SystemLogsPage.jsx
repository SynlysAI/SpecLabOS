import React, { useEffect, useState } from "react";
import { Button, Card, Empty, Form, Input, Select, Space, Table, Typography } from "antd";

import PageToolbar from "../components/PageToolbar";
import StatusTag from "../components/StatusTag";
import { fetchSystemLogs } from "../services/logApi";

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
 * 系统日志页。
 *
 * Returns:
 *     展示日志筛选栏和日志表格。
 */
export default function SystemLogsPage() {
  const [form] = Form.useForm();
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [loadFailed, setLoadFailed] = useState(false);

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
      const items = await fetchSystemLogs(filters);
      setLogs(normalizeLogs(items));
      setLoadFailed(false);
    } catch (error) {
      setLogs([]);
      setLoadFailed(true);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    form.setFieldsValue({
      keyword: "",
      level: "all",
      source: "all"
    });
    loadLogs({
      keyword: "",
      level: "all",
      source: "all"
    });
  }, []);

  return (
    <section className="page-section">
      <PageToolbar />
      <Card
        title="日志检索"
      >
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
          <Form.Item style={{ marginBottom: 0 }}>
            <Space>
              <Button htmlType="submit" type="primary">
                查询
              </Button>
              <Button
                onClick={() => {
                  form.resetFields();
                  form.setFieldsValue({ keyword: "", level: "all", source: "all" });
                  loadLogs({ keyword: "", level: "all", source: "all" });
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
              <Empty description="日志接口暂不可用" />
            ) : (
              <Empty description="暂无系统日志" />
            ),
          }}
        />
      </Card>
    </section>
  );
}
