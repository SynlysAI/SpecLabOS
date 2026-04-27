import React, { useEffect, useState } from "react";
import { Alert, Button, Card, Form, Input, Select, Space, Table } from "antd";
import { ReloadOutlined } from "@ant-design/icons";

import PageToolbar from "../components/PageToolbar";
import StatusTag from "../components/StatusTag";
import { fetchSystemLogs } from "../services/logApi";

const FALLBACK_LOGS = [
  {
    id: "LOG-001",
    level: "warning",
    service_name: "workflow-engine",
    message: "步骤三执行超时，系统已发起重试。",
    created_at: "2026-04-27 11:06"
  },
  {
    id: "LOG-002",
    level: "online",
    service_name: "device-gateway",
    message: "LC-MS-02 心跳恢复正常。",
    created_at: "2026-04-27 10:58"
  },
  {
    id: "LOG-003",
    level: "running",
    service_name: "scheduler",
    message: "已调度新一批自动分析任务。",
    created_at: "2026-04-27 10:40"
  }
];

const LEVEL_OPTIONS = [
  { label: "全部级别", value: "all" },
  { label: "信息", value: "online" },
  { label: "处理中", value: "running" },
  { label: "告警", value: "warning" }
];

const columns = [
  {
    title: "级别",
    dataIndex: "level",
    key: "level",
    width: 120,
    render: (value) => <StatusTag status={value} />
  },
  { title: "服务模块", dataIndex: "service_name", key: "service_name", width: 180 },
  { title: "日志内容", dataIndex: "message", key: "message" },
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
    service_name: item.service_name || item.service || "unknown",
    message: item.message || "无日志内容",
    created_at: item.created_at || "--"
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
  const [logs, setLogs] = useState(normalizeLogs(FALLBACK_LOGS));
  const [loading, setLoading] = useState(false);
  const [usingFallbackData, setUsingFallbackData] = useState(true);

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
      setUsingFallbackData(false);
    } catch (error) {
      setLogs(normalizeLogs(FALLBACK_LOGS));
      setUsingFallbackData(true);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    form.setFieldsValue({
      keyword: "",
      level: "all"
    });
    loadLogs({
      keyword: "",
      level: "all"
    });
  }, []);

  return (
    <section className="page-section">
      <PageToolbar
        title="系统日志"
        subtitle="检索平台服务事件、任务异常和关键操作记录。"
        extra={
          <Button icon={<ReloadOutlined />} loading={loading} onClick={() => loadLogs()}>
            刷新日志
          </Button>
        }
      />
      {usingFallbackData ? (
        <Alert
          type="warning"
          showIcon
          message="日志接口暂不可用，当前展示示例日志。"
          style={{ marginBottom: 16 }}
        />
      ) : null}
      <Card title="日志检索">
        <Form form={form} layout="inline" onFinish={loadLogs} style={{ marginBottom: 16 }}>
          <Form.Item name="keyword" style={{ marginBottom: 0 }}>
            <Input allowClear placeholder="关键字搜索" style={{ width: 240 }} />
          </Form.Item>
          <Form.Item name="level" style={{ marginBottom: 0 }}>
            <Select options={LEVEL_OPTIONS} style={{ width: 140 }} />
          </Form.Item>
          <Form.Item style={{ marginBottom: 0 }}>
            <Space>
              <Button htmlType="submit" type="primary">
                查询
              </Button>
              <Button
                onClick={() => {
                  form.resetFields();
                  form.setFieldsValue({ keyword: "", level: "all" });
                  loadLogs({ keyword: "", level: "all" });
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
          pagination={{ pageSize: 10, showSizeChanger: false }}
        />
      </Card>
    </section>
  );
}
