import React, { useEffect, useState } from "react";
import {
  Button,
  Card,
  Descriptions,
  Drawer,
  Empty,
  Form,
  Input,
  Modal,
  Select,
  Space,
  Table,
  Typography,
  message,
} from "antd";
import { DeleteOutlined, PlayCircleOutlined, ReloadOutlined } from "@ant-design/icons";

import PageToolbar from "../components/PageToolbar";
import StatusTag from "../components/StatusTag";
import {
  createSmartAccessRun,
  deleteSmartAccessTemplate,
  fetchSmartAccessTemplateDetail,
  fetchSmartAccessTemplates,
} from "../services/smartaccessApi";

const { Text } = Typography;

const STATUS_OPTIONS = [
  { label: "全部状态", value: "all" },
  { label: "已发布", value: "published" },
  { label: "草稿", value: "draft" },
];

/**
 * 将对象格式化为可读 JSON 文本。
 *
 * Args:
 *     value: 需要展示的数据。
 *
 * Returns:
 *     格式化后的文本。
 */
function formatJson(value) {
  try {
    return JSON.stringify(value || {}, null, 2);
  } catch (error) {
    return "{}";
  }
}

/**
 * 解析模板默认目标设备。
 *
 * Args:
 *     detail: 模板详情。
 *
 * Returns:
 *     模板携带的默认设备标识。
 */
function resolveDefaultDevice(detail) {
  return detail?.anchor_profile || "";
}

/**
 * 解析默认 SmartAccess 执行端电脑 ID。
 *
 * Args:
 *     detail: 模板详情。
 *
 * Returns:
 *     模板来源 SmartAccess 节点标识。
 */
function resolveDefaultNode(detail) {
  return detail?.source_device_id || "";
}

/**
 * 提取接口错误中的可读提示。
 *
 * Args:
 *     error: axios 请求异常对象。
 *
 * Returns:
 *     后端返回的 detail/message 文本，未命中时返回兜底提示。
 */
function getRequestErrorMessage(error, fallback) {
  const detail = error?.response?.data?.detail;
  if (typeof detail === "string" && detail.trim()) {
    if (detail.startsWith("无设备控制权限")) {
      return "无设备控制权限，请联系管理员申请";
    }
    return detail;
  }
  if (Array.isArray(detail) && detail.length > 0) {
    return detail
      .map((item) => item?.msg || item?.message || "")
      .filter(Boolean)
      .join("；") || fallback;
  }
  const messageText = error?.response?.data?.message;
  if (typeof messageText === "string" && messageText.trim()) {
    return messageText;
  }
  return fallback;
}

/**
 * SmartAccess 模板管理页。
 *
 * Returns:
 *     模板列表、详情预览和远程运行入口。
 */
export default function SmartAccessTemplatesPage() {
  const [filterForm] = Form.useForm();
  const [runForm] = Form.useForm();
  const [templates, setTemplates] = useState([]);
  const [detail, setDetail] = useState(null);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [detailLoading, setDetailLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [loadFailed, setLoadFailed] = useState(false);

  const columns = [
    {
      title: "执行端",
      dataIndex: "source_device_id",
      key: "source_device_id",
      render: (value) => value || "--",
    },
    { title: "模板 ID", dataIndex: "template_id", key: "template_id" },
    { title: "版本", dataIndex: "template_version", key: "template_version" },
    { title: "工作流", dataIndex: "name", key: "name" },
    {
      title: "绑定设备",
      dataIndex: "anchor_profile",
      key: "anchor_profile",
      render: (value) => value || "--",
    },
    {
      title: "状态",
      dataIndex: "status",
      key: "status",
      render: (value) => <StatusTag status={value} />,
    },
    { title: "步骤数", dataIndex: "step_count", key: "step_count" },
    { title: "发布时间", dataIndex: "published_at", key: "published_at" },
    {
      title: "操作",
      key: "actions",
      render: (_, record) => (
        <Button
          type="link"
          danger
          size="small"
          icon={<DeleteOutlined />}
          onClick={(e) => {
            e.stopPropagation();
            handleDelete(record);
          }}
        >
          删除
        </Button>
      ),
    },
  ];

  /**
   * 加载模板列表。
   *
   * Args:
   *     filters: 当前筛选条件。
   */
  async function loadTemplates(filters = filterForm.getFieldsValue()) {
    setLoading(true);
    try {
      const items = await fetchSmartAccessTemplates(filters);
      setTemplates(items);
      setLoadFailed(false);
    } catch (error) {
      setTemplates([]);
      setLoadFailed(true);
    } finally {
      setLoading(false);
    }
  }

  /**
   * 打开模板详情抽屉。
   *
   * Args:
   *     record: 当前选中的模板记录。
   */
  async function openDetail(record) {
    setDrawerOpen(true);
    setDetailLoading(true);
    setDetail(record);
    runForm.setFieldsValue({
      smartaccess_node_id: resolveDefaultNode(record),
      target_device_id: resolveDefaultDevice(record),
    });
    try {
      const data = await fetchSmartAccessTemplateDetail(
        record.template_id,
        record.template_version
      );
      setDetail(data);
      runForm.setFieldsValue({
        smartaccess_node_id: resolveDefaultNode(data),
        target_device_id: resolveDefaultDevice(data),
      });
    } catch (error) {
      message.error("模板详情加载失败");
    } finally {
      setDetailLoading(false);
    }
  }

  /**
   * 发起 SmartAccess 运行。
   *
   * Args:
   *     values: 运行表单数据。
   */
  async function submitRun(values) {
    if (!detail?.template_id || !detail?.template_version) return;

    setSubmitting(true);
    try {
      await createSmartAccessRun({
        template_id: detail.template_id,
        template_version: detail.template_version,
        smartaccess_node_id: values.smartaccess_node_id || resolveDefaultNode(detail),
        target_device_id: values.target_device_id || resolveDefaultDevice(detail),
        requested_by: "web",
      });
      message.success("SmartAccess 运行已发起");
    } catch (error) {
      message.error(
        `SmartAccess 运行发起失败：${getRequestErrorMessage(error, "请稍后重试")}`
      );
    } finally {
      setSubmitting(false);
    }
  }

  /**
   * 删除模板。
   *
   * Args:
   *     record: 模板记录。
   */
  function handleDelete(record) {
    Modal.confirm({
      title: "确认删除",
      content: `确定要删除模板 ${record.template_id}@${record.template_version} 吗？`,
      okText: "确认删除",
      okType: "danger",
      cancelText: "取消",
      onOk: async () => {
        try {
          await deleteSmartAccessTemplate(record.template_id, record.template_version);
          message.success("模板已删除");
          loadTemplates();
        } catch {
          message.error("模板删除失败");
        }
      },
    });
  }

  useEffect(() => {
    filterForm.setFieldsValue({
      keyword: "",
      device_id: "",
      status: "all",
    });
    loadTemplates({
      keyword: "",
      device_id: "",
      status: "all",
    });
  }, []);

  return (
    <section className="page-section">
      <PageToolbar />
      <div style={{ marginBottom: 16 }}>
        <Text type="secondary">
          SmartAccess 工作流模板管理，由 SmartAccess 桌面端发布，可在平台查看模板版本并远程发起运行。
        </Text>
      </div>
      <Card
        title="工作流模板"
        extra={
          <Form form={filterForm} layout="inline" onFinish={loadTemplates}>
            <Form.Item name="keyword" style={{ marginBottom: 0 }}>
              <Input allowClear placeholder="搜索模板 ID 或工作流" style={{ width: 220 }} />
            </Form.Item>
            <Form.Item name="device_id" style={{ marginBottom: 0 }}>
              <Input allowClear placeholder="目标设备" style={{ width: 180 }} />
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
                    filterForm.resetFields();
                    filterForm.setFieldsValue({
                      keyword: "",
                      device_id: "",
                      status: "all",
                    });
                    loadTemplates({
                      keyword: "",
                      device_id: "",
                      status: "all",
                    });
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
          rowKey={(record) => `${record.template_id}:${record.template_version}`}
          columns={columns}
          dataSource={templates}
          loading={loading}
          pagination={{ pageSize: 8, showSizeChanger: false }}
          locale={{
            emptyText: loadFailed ? (
              <Empty description="模板接口暂不可用" />
            ) : (
              <Empty description="暂无 SmartAccess 模板" />
            ),
          }}
          onRow={(record) => ({
            onClick: () => openDetail(record),
            style: { cursor: "pointer" },
          })}
        />
      </Card>
      <Drawer
        title={detail ? `${detail.template_id}@${detail.template_version}` : "模板详情"}
        width={720}
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        destroyOnClose
      >
        <Space direction="vertical" size={16} style={{ width: "100%" }}>
          <Descriptions column={1} size="small" bordered>
            <Descriptions.Item label="工作流">{detail?.name || "--"}</Descriptions.Item>
            <Descriptions.Item label="模板状态">
              <StatusTag status={detail?.status} />
            </Descriptions.Item>
            <Descriptions.Item label="绑定设备">
              {detail?.anchor_profile || "--"}
            </Descriptions.Item>
            <Descriptions.Item label="发布执行端">
              {detail?.source_device_id || "--"}
            </Descriptions.Item>
            <Descriptions.Item label="步骤数">
              {detail?.step_count ?? detail?.workflow?.steps?.length ?? "--"}
            </Descriptions.Item>
            <Descriptions.Item label="发布时间">
              {detail?.published_at || "--"}
            </Descriptions.Item>
          </Descriptions>
          <Form form={runForm} layout="vertical" onFinish={submitRun}>
            <Form.Item
              label="SmartAccess 执行端电脑"
              name="smartaccess_node_id"
              rules={[{ required: true, message: "请输入 SmartAccess 执行端电脑 ID" }]}
            >
              <Input placeholder="例如 lab-pc-01" />
            </Form.Item>
            <Form.Item
              label="目标设备/软件"
              name="target_device_id"
              rules={[{ required: true, message: "请输入目标设备或软件标识" }]}
            >
              <Input placeholder="例如 vpn软件、weixin" />
            </Form.Item>
            <Button
              type="primary"
              htmlType="submit"
              icon={<PlayCircleOutlined />}
              loading={submitting}
              disabled={detailLoading}
            >
              发起运行
            </Button>
          </Form>
          <Card size="small" title="模板工作流">
            <pre
              style={{
                margin: 0,
                padding: 16,
                borderRadius: 8,
                background: "#f7f8fc",
                overflowX: "auto",
                whiteSpace: "pre-wrap",
                wordBreak: "break-word",
                fontSize: 13,
                lineHeight: 1.6,
              }}
            >
              {formatJson(detail?.workflow)}
            </pre>
          </Card>
        </Space>
      </Drawer>
    </section>
  );
}
