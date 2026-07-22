import React, { useEffect, useState } from "react";
import {
  Button,
  Card,
  Descriptions,
  Drawer,
  Empty,
  Form,
  Input,
  Space,
  Table,
  Tag,
  Typography,
} from "antd";
import { ReloadOutlined } from "@ant-design/icons";

import PageToolbar from "../components/PageToolbar";
import {
  fetchExternalExperimentDispatchDetail,
  fetchExternalExperimentDispatches,
} from "../services/externalExperimentDispatchApi";

const { Text } = Typography;

/**
 * 格式化来源名称。
 *
 * Args:
 *     record: 外部实验任务列表记录。
 *
 * Returns:
 *     面向用户展示的来源文本。
 */
function formatSource(record) {
  const system = record.source_system || "未知系统";
  const module = record.source_module || "未知模块";
  return `${system} / ${module}`;
}

/**
 * 格式化关联来源信息。
 *
 * Args:
 *     sourceReference: 外部来源关联信息。
 *
 * Returns:
 *     可读的关联来源文本。
 */
function formatSourceReference(sourceReference) {
  if (!sourceReference || typeof sourceReference !== "object") {
    return "--";
  }
  return sourceReference.session_id || sourceReference.recommendation_id || "--";
}

/**
 * 渲染已接收任务状态。
 *
 * Args:
 *     status: 任务当前状态。
 *
 * Returns:
 *     状态标签组件。
 */
function renderDispatchStatus(status) {
  if (status === "received") {
    return <Tag color="blue">已接收</Tag>;
  }
  return <Tag>{status || "未知"}</Tag>;
}

/**
 * 外部实验任务页面。
 *
 * Returns:
 *     外部来源下发实验任务的列表与详情展示。
 */
export default function ExternalExperimentDispatchesPage() {
  const [form] = Form.useForm();
  const [dispatches, setDispatches] = useState([]);
  const [loading, setLoading] = useState(false);
  const [loadFailed, setLoadFailed] = useState(false);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [detailLoading, setDetailLoading] = useState(false);
  const [detail, setDetail] = useState(null);

  /**
   * 加载外部实验任务列表。
   *
   * Args:
   *     filters: 查询筛选条件。
   */
  async function loadDispatches(filters = form.getFieldsValue()) {
    setLoading(true);
    try {
      const items = await fetchExternalExperimentDispatches(filters);
      setDispatches(items);
      setLoadFailed(false);
    } catch (_error) {
      setDispatches([]);
      setLoadFailed(true);
    } finally {
      setLoading(false);
    }
  }

  /**
   * 打开并加载外部实验任务详情。
   *
   * Args:
   *     dispatchId: 外部实验任务批次标识。
   */
  async function openDetail(dispatchId) {
    setDrawerOpen(true);
    setDetail(null);
    setDetailLoading(true);
    try {
      setDetail(await fetchExternalExperimentDispatchDetail(dispatchId));
    } finally {
      setDetailLoading(false);
    }
  }

  useEffect(() => {
    form.setFieldsValue({ keyword: "" });
    loadDispatches({ keyword: "" });
  }, []);

  const columns = [
    {
      title: "状态",
      dataIndex: "status",
      key: "status",
      render: renderDispatchStatus,
    },
    { title: "实验任务", dataIndex: "experiment_name", key: "experiment_name" },
    {
      title: "来源",
      key: "source",
      render: (_, record) => formatSource(record),
    },
    {
      title: "实验对象",
      key: "experiment_object",
      render: (_, record) => {
        const object = record.experiment_object || {};
        return object.type ? `${object.name}（${object.type}）` : object.name || "--";
      },
    },
    { title: "条件组数", dataIndex: "condition_count", key: "condition_count" },
    {
      title: "关联来源",
      dataIndex: "source_reference",
      key: "source_reference",
      render: formatSourceReference,
    },
    { title: "下发时间", dataIndex: "received_at", key: "received_at" },
    {
      title: "操作",
      key: "actions",
      render: (_, record) => (
        <Button type="link" onClick={() => openDetail(record.dispatch_id)}>
          查看详情
        </Button>
      ),
    },
  ];

  const conditionColumns = [
    { title: "条件编号", dataIndex: "condition_id", key: "condition_id" },
    {
      title: "参数",
      dataIndex: "parameters",
      key: "parameters",
      render: (value) => <Text code>{JSON.stringify(value || {})}</Text>,
    },
    {
      title: "附加信息",
      dataIndex: "metadata",
      key: "metadata",
      render: (value) => <Text code>{JSON.stringify(value || {})}</Text>,
    },
  ];

  return (
    <section className="page-section">
      <PageToolbar />
      <Card title="外部实验任务">
        <Form form={form} layout="inline" onFinish={loadDispatches}>
          <Form.Item name="keyword" label="关键词">
            <Input allowClear placeholder="任务、对象或来源" style={{ width: 240 }} />
          </Form.Item>
          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit">
                查询
              </Button>
              <Button icon={<ReloadOutlined />} onClick={() => loadDispatches()}>
                刷新
              </Button>
            </Space>
          </Form.Item>
        </Form>

        <div style={{ marginTop: 16 }}>
          {loadFailed ? (
            <Empty description="外部实验任务加载失败，请稍后重试" />
          ) : (
            <Table
              rowKey="dispatch_id"
              loading={loading}
              columns={columns}
              dataSource={dispatches}
              pagination={{ pageSize: 10 }}
              locale={{ emptyText: "暂无外部实验任务" }}
              scroll={{ x: 1050 }}
            />
          )}
        </div>
      </Card>

      <Drawer
        title="外部实验任务详情"
        width={840}
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
      >
        {detailLoading ? (
          <Empty description="正在加载任务详情" />
        ) : detail ? (
          <Space direction="vertical" size={16} style={{ width: "100%" }}>
            <Descriptions bordered size="small" column={1}>
              <Descriptions.Item label="任务编号">
                {detail.dispatch_id}
              </Descriptions.Item>
              <Descriptions.Item label="状态">
                {renderDispatchStatus(detail.status)}
              </Descriptions.Item>
              <Descriptions.Item label="实验任务">
                {detail.experiment_name}
              </Descriptions.Item>
              <Descriptions.Item label="来源">
                {formatSource(detail)}
              </Descriptions.Item>
              <Descriptions.Item label="实验对象">
                {detail.experiment_object?.name || "--"}
              </Descriptions.Item>
              <Descriptions.Item label="对象类型">
                {detail.experiment_object?.type || "--"}
              </Descriptions.Item>
              <Descriptions.Item label="实验说明">
                {detail.experiment_content || "--"}
              </Descriptions.Item>
              <Descriptions.Item label="优化上下文">
                <Text code>{JSON.stringify(detail.optimization_context || {})}</Text>
              </Descriptions.Item>
            </Descriptions>
            <Table
              rowKey="condition_id"
              columns={conditionColumns}
              dataSource={detail.conditions || []}
              pagination={false}
              scroll={{ x: 700 }}
            />
          </Space>
        ) : null}
      </Drawer>
    </section>
  );
}
