import React, { useEffect, useState } from "react";
import { Button, Card, Empty, Form, Input, Select, Space, Table, Typography } from "antd";
import { useNavigate } from "react-router-dom";

import PageToolbar from "../components/PageToolbar";
import StatusTag from "../components/StatusTag";
import { fetchWorkflowRuns } from "../services/workflowApi";

const { Text } = Typography;

const STATUS_OPTIONS = [
  { label: "全部状态", value: "all" },
  { label: "排队中", value: "queued" },
  { label: "运行中", value: "running" },
  { label: "已完成", value: "success" },
  { label: "失败", value: "failed" },
  { label: "阻塞", value: "blocked" },
  { label: "已取消", value: "cancelled" },
];

const columns = [
  { title: "运行编号", dataIndex: "run_id", key: "run_id" },
  { title: "工作流名称", dataIndex: "workflow_name", key: "workflow_name" },
  {
    title: "目标设备",
    dataIndex: "device_key",
    key: "device_key",
    render: (value) => value || "--",
  },
  {
    title: "状态",
    dataIndex: "status",
    key: "status",
    render: (value) => <StatusTag status={value} />,
  },
  {
    title: "当前步骤",
    dataIndex: "current_step_index",
    key: "current_step_index",
    render: (value, record) => `${value}/${record.total_steps || value}`,
  },
  { title: "启动时间", dataIndex: "started_at", key: "started_at" },
];

function normalizeRuns(items) {
  return items.map((item, index) => ({
    run_id: item.run_id || item.id || `run-${index}`,
    workflow_name: item.workflow_name || item.workflow?.name || "未命名工作流",
    device_key: item.device_key || "--",
    status: item.status || "idle",
    current_step_index: item.current_step_index || 0,
    total_steps: item.total_steps || item.steps?.length || 0,
    started_at: item.started_at || "--",
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
  const [runs, setRuns] = useState([]);
  const [loading, setLoading] = useState(false);
  const [loadFailed, setLoadFailed] = useState(false);

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
      const items = await fetchWorkflowRuns({ ...filters, source: "speclabos" });
      setRuns(normalizeRuns(items));
      setLoadFailed(false);
    } catch (error) {
      setRuns([]);
      setLoadFailed(true);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    form.setFieldsValue({ keyword: "", status: "all" });
    loadRuns({ keyword: "", status: "all" });
  }, []);

  return (
    <section className="page-section">
      <PageToolbar />
      <Text type="secondary" style={{ display: "block", marginBottom: 16 }}>
        查看由 SpecLabOS 工作流编排下发执行的任务记录。
      </Text>
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
          locale={{
            emptyText: loadFailed ? (
              <Empty description="运行记录接口暂不可用" />
            ) : (
              <Empty description="暂无任务运行记录" />
            ),
          }}
          onRow={(record) => ({
            onClick: () => navigate(`/runs/${record.run_id}`),
            style: { cursor: "pointer" }
          })}
        />
      </Card>
    </section>
  );
}
