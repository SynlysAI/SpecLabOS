import React, { useEffect, useState } from "react";
import { Alert, Button, Card, Form, Input, Select, Space, Table } from "antd";
import { ReloadOutlined } from "@ant-design/icons";
import { useNavigate } from "react-router-dom";

import PageToolbar from "../components/PageToolbar";
import StatusTag from "../components/StatusTag";
import { http } from "../services/http";

const FALLBACK_RUNS = [
  {
    run_id: "RUN-20260427-001",
    workflow_name: "样品全流程分析",
    status: "running",
    current_step_index: 2,
    total_steps: 4,
    started_at: "2026-04-27 10:15"
  },
  {
    run_id: "RUN-20260427-002",
    workflow_name: "核磁复测任务",
    status: "warning",
    current_step_index: 3,
    total_steps: 3,
    started_at: "2026-04-27 09:40"
  },
  {
    run_id: "RUN-20260426-008",
    workflow_name: "红外谱图导出",
    status: "online",
    current_step_index: 3,
    total_steps: 3,
    started_at: "2026-04-26 18:05"
  }
];

const STATUS_OPTIONS = [
  { label: "全部状态", value: "all" },
  { label: "运行中", value: "running" },
  { label: "已完成", value: "online" },
  { label: "告警", value: "warning" }
];

const columns = [
  { title: "运行编号", dataIndex: "run_id", key: "run_id" },
  { title: "工作流名称", dataIndex: "workflow_name", key: "workflow_name" },
  {
    title: "状态",
    dataIndex: "status",
    key: "status",
    render: (value) => <StatusTag status={value} />
  },
  {
    title: "当前步骤",
    dataIndex: "current_step_index",
    key: "current_step_index",
    render: (value, record) => `${value}/${record.total_steps || value}`
  },
  { title: "启动时间", dataIndex: "started_at", key: "started_at" }
];

/**
 * 获取运行记录列表。
 *
 * Args:
 *     filters: 页面筛选条件。
 *
 * Returns:
 *     运行记录列表。
 */
async function fetchWorkflowRuns(filters) {
  const response = await http.get("/api/workflow-runs", {
    params: {
      keyword: filters.keyword || undefined,
      status: filters.status && filters.status !== "all" ? filters.status : undefined
    }
  });
  return response.data.items || [];
}

/**
 * 规范运行记录列表数据。
 *
 * Args:
 *     items: 原始运行记录列表。
 *
 * Returns:
 *     可直接供表格使用的运行记录。
 */
function normalizeRuns(items) {
  return items.map((item, index) => ({
    run_id: item.run_id || item.id || `run-${index}`,
    workflow_name: item.workflow_name || item.workflow?.name || "未命名工作流",
    status: item.status || "idle",
    current_step_index: item.current_step_index || 0,
    total_steps: item.total_steps || item.steps?.length || 0,
    started_at: item.started_at || "--"
  }));
}

/**
 * 任务运行页。
 *
 * Returns:
 *     展示运行记录表格与基础筛选栏。
 */
export default function WorkflowRunsPage() {
  const navigate = useNavigate();
  const [form] = Form.useForm();
  const [runs, setRuns] = useState(normalizeRuns(FALLBACK_RUNS));
  const [loading, setLoading] = useState(false);
  const [usingFallbackData, setUsingFallbackData] = useState(true);

  /**
   * 加载运行记录列表。
   *
   * Args:
   *     filters: 当前筛选条件。
   *
   * Returns:
   *     无返回值。
   */
  async function loadRuns(filters = form.getFieldsValue()) {
    setLoading(true);
    try {
      const items = await fetchWorkflowRuns(filters);
      setRuns(normalizeRuns(items));
      setUsingFallbackData(false);
    } catch (error) {
      setRuns(normalizeRuns(FALLBACK_RUNS));
      setUsingFallbackData(true);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    form.setFieldsValue({
      keyword: "",
      status: "all"
    });
    loadRuns({
      keyword: "",
      status: "all"
    });
  }, []);

  return (
    <section className="page-section">
      <PageToolbar
        title="任务运行"
        subtitle="查看工作流执行进度、当前步骤和最近运行状态。"
        extra={
          <Button icon={<ReloadOutlined />} loading={loading} onClick={() => loadRuns()}>
            刷新列表
          </Button>
        }
      />
      {usingFallbackData ? (
        <Alert
          type="warning"
          showIcon
          message="运行记录接口暂不可用，当前展示示例数据。"
          style={{ marginBottom: 16 }}
        />
      ) : null}
      <Card
        title="运行记录列表"
        extra={
          <Form form={form} layout="inline" onFinish={loadRuns}>
            <Form.Item name="keyword" style={{ marginBottom: 0 }}>
              <Input allowClear placeholder="搜索运行编号或工作流名称" style={{ width: 220 }} />
            </Form.Item>
            <Form.Item name="status" style={{ marginBottom: 0 }}>
              <Select options={STATUS_OPTIONS} style={{ width: 140 }} />
            </Form.Item>
            <Form.Item style={{ marginBottom: 0 }}>
              <Space>
                <Button htmlType="submit" type="primary">
                  查询
                </Button>
                <Button
                  onClick={() => {
                    form.resetFields();
                    form.setFieldsValue({ keyword: "", status: "all" });
                    loadRuns({ keyword: "", status: "all" });
                  }}
                >
                  重置
                </Button>
              </Space>
            </Form.Item>
          </Form>
        }
      >
        <Table
          rowKey="run_id"
          columns={columns}
          dataSource={runs}
          loading={loading}
          pagination={{ pageSize: 8, showSizeChanger: false }}
          onRow={(record) => ({
            onClick: () => navigate(`/runs/${record.run_id}`),
            style: { cursor: "pointer" }
          })}
        />
      </Card>
    </section>
  );
}
