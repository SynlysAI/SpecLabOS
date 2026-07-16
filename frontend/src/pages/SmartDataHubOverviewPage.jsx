import React, { useEffect, useMemo, useState } from "react";
import {
  Alert,
  Button,
  Card,
  Col,
  Descriptions,
  Drawer,
  Empty,
  Form,
  Input,
  Row,
  Select,
  Space,
  Statistic,
  Table,
  Tag,
  Tooltip,
  Typography
} from "antd";
import {
  DatabaseOutlined,
  FileSearchOutlined,
  HddOutlined,
  ReloadOutlined
} from "@ant-design/icons";

import PageToolbar from "../components/PageToolbar";
import StatusTag from "../components/StatusTag";
import {
  fetchDataAssetFiles,
  fetchDataAssetOverview,
  fetchDataAssets
} from "../services/dataAssetApi";

const { Paragraph, Text } = Typography;

const DEFAULT_OVERVIEW = {
  asset_count: 0,
  file_count: 0,
  total_size: 0,
  device_count: 0,
  collector_count: 0,
  latest_ingested_at: "",
  data_type_distribution: [],
  device_distribution: [],
  collector_distribution: []
};

const DEFAULT_FILTERS = {
  keyword: "",
  device_id: "",
  collector_id: "",
  data_type: "all",
  limit: 100
};

const CHART_COLORS = ["#1677ff", "#52c41a", "#faad14", "#722ed1", "#13c2c2", "#f5222d"];

/**
 * 格式化文件大小。
 *
 * Args:
 *     value: 字节数。
 *
 * Returns:
 *     带单位的文件大小文本。
 */
function formatBytes(value) {
  const size = Number(value || 0);
  if (size < 1024) return `${size} B`;
  if (size < 1024 ** 2) return `${(size / 1024).toFixed(1)} KB`;
  if (size < 1024 ** 3) return `${(size / 1024 ** 2).toFixed(1)} MB`;
  return `${(size / 1024 ** 3).toFixed(1)} GB`;
}

/**
 * 格式化 ISO 时间文本。
 *
 * Args:
 *     value: 后端返回的时间文本。
 *
 * Returns:
 *     去掉时区和微秒后的短时间文本。
 */
function formatDateTime(value) {
  if (!value) return "--";
  return String(value)
    .replace(/([+-]\d{2}:?\d{2}|Z)$/u, "")
    .replace("T", " ")
    .split(".")[0];
}

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
 * 规范资产列表项。
 *
 * Args:
 *     items: 后端返回的数据资产列表。
 *
 * Returns:
 *     表格可直接使用的资产列表。
 */
function normalizeAssets(items) {
  return items.map((item, index) => ({
    ...item,
    row_key: item.asset_id || `asset-${index}`,
    display_name: item.root_name || item.filename || item.asset_group_id || "未命名资产",
    file_count: Number(item.file_count || 0),
    total_size: Number(item.total_size || 0),
    upload_status: item.upload_status || "pending"
  }));
}

/**
 * 按分布数据生成下拉选项。
 *
 * Args:
 *     distribution: 概览接口返回的分布列表。
 *
 * Returns:
 *     Select 组件选项。
 */
function buildOptions(distribution) {
  return [
    { label: "全部类型", value: "all" },
    ...(distribution || []).map((item) => ({
      label: item.label || item.key,
      value: item.key
    }))
  ];
}

/**
 * 按设备分布数据生成设备下拉选项。
 *
 * Args:
 *     distribution: 概览接口返回的设备分布列表。
 *
 * Returns:
 *     设备 Select 组件选项。
 */
function buildDeviceOptions(distribution) {
  return (distribution || []).map((item) => ({
    label: `${item.label || item.key}（${item.asset_count} 资产 / ${item.file_count} 文件）`,
    value: item.key
  }));
}

/**
 * 构造环形图渐变背景。
 *
 * Args:
 *     items: 分布数据列表。
 *
 * Returns:
 *     CSS conic-gradient 背景值。
 */
function buildConicGradient(items) {
  const totalCount = (items || []).reduce((sum, item) => sum + Number(item.asset_count || 0), 0);
  if (!totalCount) return "#eef2f7";

  let cursor = 0;
  const slices = items.slice(0, CHART_COLORS.length).map((item, index) => {
    const start = cursor;
    const percent = (Number(item.asset_count || 0) / totalCount) * 100;
    cursor += percent;
    return `${CHART_COLORS[index]} ${start}% ${cursor}%`;
  });
  return `conic-gradient(${slices.join(", ")})`;
}

/**
 * 数据资产分布卡片。
 *
 * Args:
 *     title: 卡片标题。
 *     items: 分布数据列表。
 *
 * Returns:
 *     数据分布展示卡片。
 */
function DistributionCard({ title, items }) {
  const totalCount = (items || []).reduce((sum, item) => sum + Number(item.asset_count || 0), 0);
  const visibleItems = (items || []).slice(0, CHART_COLORS.length);
  return (
    <Card title={title} size="small" style={{ height: "100%" }}>
      {items?.length ? (
        <Space size={20} align="center" style={{ width: "100%" }}>
          <div
            style={{
              width: 132,
              height: 132,
              borderRadius: "50%",
              background: buildConicGradient(visibleItems),
              position: "relative",
              flex: "0 0 auto",
              boxShadow: "inset 0 0 0 1px rgba(15, 23, 42, 0.04)"
            }}
          >
            <div
              style={{
                position: "absolute",
                inset: 28,
                borderRadius: "50%",
                background: "#fff",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                flexDirection: "column"
              }}
            >
              <Text strong style={{ fontSize: 22 }}>{(items || []).length}</Text>
              <Text type="secondary" style={{ fontSize: 12 }}>类目数</Text>
            </div>
          </div>
          <Space direction="vertical" style={{ flex: 1, minWidth: 0 }} size={10}>
            {visibleItems.map((item, index) => (
              <Space key={item.key || item.label} style={{ width: "100%", justifyContent: "space-between" }}>
                <Space size={8} style={{ minWidth: 0 }}>
                  <span
                    style={{
                      width: 10,
                      height: 10,
                      borderRadius: "50%",
                      background: CHART_COLORS[index],
                      display: "inline-block",
                      flex: "0 0 auto"
                    }}
                  />
                  <Text ellipsis style={{ maxWidth: 160 }}>{item.label || item.key}</Text>
                </Space>
                <Tooltip title={`资产 ${item.asset_count} · 文件 ${item.file_count}`}>
                  <Text type="secondary" style={{ whiteSpace: "nowrap" }}>
                    {item.asset_count}
                  </Text>
                </Tooltip>
              </Space>
            ))}
          </Space>
        </Space>
      ) : (
        <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无分布数据" />
      )}
    </Card>
  );
}

/**
 * 数据概览统计卡片。
 *
 * Args:
 *     title: 指标标题。
 *     value: 指标值。
 *     icon: 指标图标。
 *     tooltip: 完整值提示。
 *
 * Returns:
 *     等高统计卡片。
 */
function OverviewStatCard({ title, value, icon, loading, tooltip }) {
  const content = (
    <Card loading={loading} style={{ height: "100%" }} bodyStyle={{ padding: 20 }}>
      <Statistic
        title={title}
        value={value || "--"}
        prefix={icon}
        valueStyle={{ fontSize: 24, lineHeight: 1.25, whiteSpace: "nowrap" }}
      />
    </Card>
  );
  return tooltip ? <Tooltip title={tooltip}>{content}</Tooltip> : content;
}

/**
 * SmartDataHub 数据概览页。
 *
 * Returns:
 *     展示数据资产概览、分布、筛选列表和文件明细。
 */
export default function SmartDataHubOverviewPage() {
  const [form] = Form.useForm();
  const [overview, setOverview] = useState(DEFAULT_OVERVIEW);
  const [assets, setAssets] = useState([]);
  const [total, setTotal] = useState(0);
  const [files, setFiles] = useState([]);
  const [selectedAsset, setSelectedAsset] = useState(null);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [overviewLoading, setOverviewLoading] = useState(false);
  const [assetsLoading, setAssetsLoading] = useState(false);
  const [filesLoading, setFilesLoading] = useState(false);
  const [loadFailed, setLoadFailed] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");
  const [selectedDeviceId, setSelectedDeviceId] = useState("");

  const dataTypeOptions = useMemo(
    () => buildOptions(overview.data_type_distribution),
    [overview.data_type_distribution]
  );
  const deviceOptions = useMemo(
    () => buildDeviceOptions(overview.device_distribution),
    [overview.device_distribution]
  );

  const columns = [
    {
      title: "资产名称",
      dataIndex: "display_name",
      key: "display_name",
      render: (value, record) => (
        <div>
          <Text strong>{value}</Text>
          <br />
          <Text type="secondary" style={{ fontSize: 12 }}>
            {record.asset_group_id || record.asset_id}
          </Text>
        </div>
      )
    },
    {
      title: "数据类型",
      dataIndex: "data_type",
      key: "data_type",
      width: 140,
      render: (value) => <Tag color="blue">{value || "unknown"}</Tag>
    },
    { title: "设备", dataIndex: "device_id", key: "device_id", width: 160 },
    { title: "采集器", dataIndex: "collector_id", key: "collector_id", width: 160 },
    {
      title: "资产类型",
      dataIndex: "asset_kind",
      key: "asset_kind",
      width: 110,
      render: (value) => value || "file"
    },
    { title: "文件数", dataIndex: "file_count", key: "file_count", width: 90 },
    {
      title: "总大小",
      dataIndex: "total_size",
      key: "total_size",
      width: 110,
      render: (value) => formatBytes(value)
    },
    {
      title: "状态",
      dataIndex: "upload_status",
      key: "upload_status",
      width: 110,
      render: (value) => <StatusTag status={value} />
    },
    {
      title: "入库时间",
      dataIndex: "ingested_at",
      key: "ingested_at",
      width: 170,
      render: (value) => (
        <Tooltip title={value || "--"}>
          <span>{formatDateTime(value)}</span>
        </Tooltip>
      )
    }
  ];

  const fileColumns = [
    { title: "相对路径", dataIndex: "relative_path", key: "relative_path" },
    { title: "文件名", dataIndex: "filename", key: "filename", width: 180 },
    {
      title: "大小",
      dataIndex: "file_size",
      key: "file_size",
      width: 100,
      render: (value) => formatBytes(value)
    },
    { title: "类型", dataIndex: "content_type", key: "content_type", width: 170 },
    { title: "状态", dataIndex: "upload_status", key: "upload_status", width: 110 }
  ];

  /**
   * 加载数据资产概览。
   */
  async function loadOverview() {
    setOverviewLoading(true);
    try {
      const data = await fetchDataAssetOverview();
      setOverview({ ...DEFAULT_OVERVIEW, ...data });
    } catch (error) {
      console.error("加载 SmartDataHub 概览失败", error);
      setOverview(DEFAULT_OVERVIEW);
      setLoadFailed(true);
      setErrorMessage(buildRequestErrorMessage(error));
    } finally {
      setOverviewLoading(false);
    }
  }

  /**
   * 加载数据资产列表。
   *
   * Args:
   *     filters: 查询筛选条件。
   */
  async function loadAssets(filters = form.getFieldsValue()) {
    setAssetsLoading(true);
    try {
      const response = await fetchDataAssets({ ...DEFAULT_FILTERS, ...filters });
      setAssets(normalizeAssets(response.items));
      setTotal(response.total);
      setLoadFailed(false);
      setErrorMessage("");
    } catch (error) {
      console.error("加载 SmartDataHub 数据资产失败", error);
      setAssets([]);
      setTotal(0);
      setLoadFailed(true);
      setErrorMessage(buildRequestErrorMessage(error));
    } finally {
      setAssetsLoading(false);
    }
  }

  /**
   * 刷新概览和资产列表。
   */
  function refreshAll() {
    loadOverview();
    loadAssets(form.getFieldsValue());
  }

  /**
   * 打开资产详情抽屉。
   *
   * Args:
   *     asset: 当前选中的数据资产。
   */
  async function openAssetDetail(asset) {
    setSelectedAsset(asset);
    setDrawerOpen(true);
    setFiles([]);
    setFilesLoading(true);
    try {
      const items = await fetchDataAssetFiles(asset.asset_id);
      setFiles(items);
    } catch (error) {
      console.error("加载 SmartDataHub 文件明细失败", error);
      setFiles([]);
    } finally {
      setFilesLoading(false);
    }
  }

  useEffect(() => {
    form.setFieldsValue(DEFAULT_FILTERS);
    setSelectedDeviceId(DEFAULT_FILTERS.device_id);
    loadOverview();
    loadAssets(DEFAULT_FILTERS);
  }, []);

  return (
    <section className="page-section">
      <PageToolbar />
      {loadFailed && errorMessage ? (
        <Alert type="error" showIcon message="数据加载失败" description={errorMessage} style={{ marginBottom: 16 }} />
      ) : null}

      <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
        <Col xs={24} sm={12} lg={5}>
          <OverviewStatCard
            title="资产总数"
            value={overview.asset_count}
            icon={<DatabaseOutlined />}
            loading={overviewLoading}
          />
        </Col>
        <Col xs={24} sm={12} lg={5}>
          <OverviewStatCard
            title="文件总数"
            value={overview.file_count}
            icon={<FileSearchOutlined />}
            loading={overviewLoading}
          />
        </Col>
        <Col xs={24} sm={12} lg={5}>
          <OverviewStatCard
            title="存储总量"
            value={formatBytes(overview.total_size)}
            icon={<HddOutlined />}
            loading={overviewLoading}
          />
        </Col>
        <Col xs={24} sm={12} lg={5}>
          <OverviewStatCard title="接入设备数" value={overview.device_count} loading={overviewLoading} />
        </Col>
        <Col xs={24} sm={12} lg={4}>
          <OverviewStatCard title="采集器数" value={overview.collector_count} loading={overviewLoading} />
        </Col>
      </Row>

      <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
        <Col xs={24} lg={8}>
          <DistributionCard title="按数据类型分布" items={overview.data_type_distribution} />
        </Col>
        <Col xs={24} lg={8}>
          <DistributionCard title="按设备分布" items={overview.device_distribution} />
        </Col>
        <Col xs={24} lg={8}>
          <DistributionCard title="按采集器分布" items={overview.collector_distribution} />
        </Col>
      </Row>

      <Card
        title="按设备查看数据资产"
        extra={
          <Button icon={<ReloadOutlined />} onClick={refreshAll}>
            刷新
          </Button>
        }
      >
        <Form
          form={form}
          layout="inline"
          onFinish={loadAssets}
          onValuesChange={(_, values) => setSelectedDeviceId(values.device_id || "")}
          style={{ marginBottom: 16 }}
        >
          <Form.Item name="device_id" label="设备" style={{ marginBottom: 8 }}>
            <Select
              allowClear
              showSearch
              placeholder="先选择设备查看数据资产"
              options={deviceOptions}
              optionFilterProp="label"
              style={{ width: 320 }}
            />
          </Form.Item>
          <Form.Item name="keyword" style={{ marginBottom: 8 }}>
            <Input allowClear placeholder="搜索资产名 / 文件名 / 资产组" style={{ width: 220 }} />
          </Form.Item>
          <Form.Item name="collector_id" style={{ marginBottom: 8 }}>
            <Input allowClear placeholder="Collector ID" style={{ width: 150 }} />
          </Form.Item>
          <Form.Item name="data_type" style={{ marginBottom: 8 }}>
            <Select options={dataTypeOptions} style={{ width: 150 }} />
          </Form.Item>
          <Form.Item style={{ marginBottom: 8 }}>
            <Space>
              <Button htmlType="submit" type="primary">
                查询
              </Button>
              <Button
                onClick={() => {
                  form.setFieldsValue(DEFAULT_FILTERS);
                  setSelectedDeviceId(DEFAULT_FILTERS.device_id);
                  loadAssets(DEFAULT_FILTERS);
                }}
              >
                重置
              </Button>
            </Space>
          </Form.Item>
        </Form>
        <Text type="secondary" style={{ display: "block", marginBottom: 12 }}>
          {selectedDeviceId
            ? `当前设备筛选匹配 ${total} 条资产，表格最多展示 ${form.getFieldValue("limit") || DEFAULT_FILTERS.limit} 条。`
            : `请选择设备查看对应数据资产；未选择时展示最近 ${form.getFieldValue("limit") || DEFAULT_FILTERS.limit} 条资产。`}
        </Text>
        <Table
          rowKey="row_key"
          columns={columns}
          dataSource={assets}
          loading={assetsLoading}
          pagination={{ pageSize: 10, showSizeChanger: false }}
          scroll={{ x: 1200 }}
          locale={{ emptyText: <Empty description={loadFailed ? "数据资产接口暂不可用" : "暂无 SmartDataHub 数据资产"} /> }}
          onRow={(record) => ({
            onClick: () => openAssetDetail(record),
            style: { cursor: "pointer" }
          })}
        />
      </Card>

      <Drawer
        title={selectedAsset?.display_name || "数据资产详情"}
        open={drawerOpen}
        width={900}
        onClose={() => setDrawerOpen(false)}
        destroyOnClose
      >
        {selectedAsset ? (
          <Space direction="vertical" size={16} style={{ width: "100%" }}>
            <Descriptions bordered column={2} size="small" title="资产信息">
              <Descriptions.Item label="资产 ID" span={2}>{selectedAsset.asset_id}</Descriptions.Item>
              <Descriptions.Item label="资产组">{selectedAsset.asset_group_id || "--"}</Descriptions.Item>
              <Descriptions.Item label="数据类型">{selectedAsset.data_type || "--"}</Descriptions.Item>
              <Descriptions.Item label="设备 ID">{selectedAsset.device_id || "--"}</Descriptions.Item>
              <Descriptions.Item label="Collector ID">{selectedAsset.collector_id || "--"}</Descriptions.Item>
              <Descriptions.Item label="文件数">{selectedAsset.file_count}</Descriptions.Item>
              <Descriptions.Item label="总大小">{formatBytes(selectedAsset.total_size)}</Descriptions.Item>
              <Descriptions.Item label="创建时间">{formatDateTime(selectedAsset.created_at)}</Descriptions.Item>
              <Descriptions.Item label="入库时间">{formatDateTime(selectedAsset.ingested_at)}</Descriptions.Item>
            </Descriptions>

            <Descriptions bordered column={1} size="small" title="存储信息">
              <Descriptions.Item label="Bucket">{selectedAsset.storage_bucket || "--"}</Descriptions.Item>
              <Descriptions.Item label="Prefix">{selectedAsset.storage_prefix || "--"}</Descriptions.Item>
              <Descriptions.Item label="URI">{selectedAsset.storage_uri || "--"}</Descriptions.Item>
            </Descriptions>

            <Card title="文件清单" size="small">
              <Table
                rowKey="file_id"
                columns={fileColumns}
                dataSource={files}
                loading={filesLoading}
                pagination={{ pageSize: 8, showSizeChanger: false }}
                scroll={{ x: 900 }}
                locale={{ emptyText: <Empty description="暂无文件明细" /> }}
              />
            </Card>

            <Card title="元数据" size="small">
              <Paragraph copyable style={{ whiteSpace: "pre-wrap", marginBottom: 0 }}>
                {JSON.stringify(selectedAsset.metadata || {}, null, 2)}
              </Paragraph>
            </Card>
          </Space>
        ) : null}
      </Drawer>
    </section>
  );
}
