import React, { useEffect, useState } from "react";
import { Button, Card, Empty, Form, Input, Select, Space, Table, Typography } from "antd";
import { ReloadOutlined } from "@ant-design/icons";
import { useNavigate } from "react-router-dom";

import PageToolbar from "../components/PageToolbar";
import StatusTag from "../components/StatusTag";
import { fetchSmartAccessRuns } from "../services/smartaccessApi";

const { Text } = Typography;

const STATUS_OPTIONS = [
  { label: "全部状态", value: "all" },
  { label: "排队中", value: "queued" },
  { label: "已接收", value: "accepted" },
  { label: "运行中", value: "running" },
  { label: "已完成", value: "success" },
  { label: "失败", value: "failed" },
  { label: "阻塞", value: "blocked" },
  { label: "已拒绝", value: "rejected" },
];

const columns = [
  { title: "运行编号", dataIndex: "run_id", key: "run_id" },
  { title: "工作流名称", dataIndex: "workflow_name", key: "workflow_name" },
  {
    title: "执行端",
    dataIndex: "smartaccess_node_id",
    key: "smartaccess_node_id",
    render: (value) => value || "--",
  },
  {
    title: "目标设备",
    dataIndex: "target_device_id",
    key: "target_device_id",
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
  return items.map((item) => ({
    run_id: item.run_id || item.id || "--",
    workflow_name: item.workflow_name || "未命名工作流",
    smartaccess_node_id: item.smartaccess_node_id || "--",
    target_device_id: item.target_device_id || "--",
    status: item.status || "queued",
    current_step_index: item.current_step_index || 0,
    total_steps: item.total_steps || 0,
    started_at: item.started_at || "--",
  }));
}

/**
 * SmartAccess 任务运行页。
 *
 * Returns:
 *     SmartAccess 远程运行记录表格与筛选栏。
 */
export default function SmartAccessRunsPage() {
  const navigate = useNavigate();
  const [form] = Form.useForm();
  const [runs, setRuns] = useState([]);
  const [loading, setLoading] = useState(false);
  const [loadFailed, setLoadFailed] = useState(false);

  async function loadRuns(filters = form.getFieldsValue()) {
    setLoading(true);
    try {
      const items = await fetchSmartAccessRuns(filters);
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
      <div style={{ marginBottom: 16 }}>
        <Text type="secondary">
          SmartAccess 远程任务运行记录，由 SpecLabOS 发起并下发到指定执行端电脑执行。
        </Text>
      </div>
      <Card
        title="SmartAccess 任务运行"
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
                  icon={<ReloadOutlined />}
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
              <Empty description="暂无 SmartAccess 任务运行记录" />
            ),
          }}
          onRow={(record) => ({
            onClick: () => navigate(`/smartaccess/runs/${record.run_id}`),
            style: { cursor: "pointer" },
          })}
        />
      </Card>
    </section>
  );
}
