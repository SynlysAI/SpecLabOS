import React, { useEffect, useMemo, useState } from "react";
import {
  Alert,
  Button,
  Card,
  Col,
  Descriptions,
  Drawer,
  Empty,
  Row,
  Space,
  Statistic,
  Table,
  Tag,
  Tooltip,
  Typography
} from "antd";
import {
  CloudServerOutlined,
  DatabaseOutlined,
  FileSearchOutlined,
  HddOutlined,
  ReloadOutlined
} from "@ant-design/icons";

import PageToolbar from "../components/PageToolbar";
import StatusTag from "../components/StatusTag";
import {
  fetchDataAssetFiles,
  fetchDataAssets,
  fetchDataDeviceStats
} from "../services/dataAssetApi";

const { Text } = Typography;

const DEFAULT_OVERVIEW = {
  asset_count: 0,
  file_count: 0,
  total_size: 0,
  device_count: 0,
  collector_count: 0,
  latest_ingested_at: ""
};

const DEFAULT_ASSET_LIMIT = 100;

function formatBytes(value) {
  const size = Number(value || 0);
  if (size < 1024) return `${size} B`;
  if (size < 1024 ** 2) return `${(size / 1024).toFixed(1)} KB`;
  if (size < 1024 ** 3) return `${(size / 1024 ** 2).toFixed(1)} MB`;
  return `${(size / 1024 ** 3).toFixed(1)} GB`;
}

function formatDateTime(value) {
  if (!value) return "--";
  return String(value)
    .replace(/([+-]\d{2}:?\d{2}|Z)$/u, "")
    .replace("T", " ")
    .split(".")[0];
}

function buildRequestErrorMessage(error) {
  const baseUrl = error?.config?.baseURL || "http://127.0.0.1:8000";
  const requestPath = error?.config?.url || "";
  const detail = error?.response?.data?.detail;
  if (typeof detail === "string" && detail.trim()) {
    return `后端返回 ${error.response.status}：${detail}`;
  }
  if (error?.message === "Network Error") {
    return `无法连接 ${baseUrl}，请确认后端服务已启动。`;
  }
  if (error?.response?.status) {
    return `请求 ${baseUrl}${requestPath} 失败，HTTP ${error.response.status}。`;
  }
  return `请求 ${baseUrl}${requestPath || ""} 失败。`;
}

function normalizeAssets(items) {
  return (items || []).map((item, index) => ({
    ...item,
    row_key: item.asset_id || `asset-${index}`,
    display_name: item.root_name || item.filename || item.asset_group_id || "未命名资产",
    file_count: Number(item.file_count || 0),
    total_size: Number(item.total_size || 0),
    upload_status: item.upload_status || "pending"
  }));
}

function normalizeDeviceStats(items) {
  return (items || []).map((item) => ({
    ...item,
    row_key: item.device_id,
    asset_count: Number(item.asset_count || 0),
    file_count: Number(item.file_count || 0),
    total_size: Number(item.total_size || 0),
    collector_count: Number(item.collector_count || 0),
    data_type_count: Number(item.data_type_count || 0)
  }));
}

function OverviewStatCard({ title, value, icon, loading, tooltip }) {
  const displayValue = value === undefined || value === null || value === "" ? "--" : value;
  const content = (
    <Card loading={loading} style={{ height: "100%" }} styles={{ body: { padding: 18 } }}>
      <Statistic
        title={title}
        value={displayValue}
        prefix={icon}
        valueStyle={{ fontSize: 23, lineHeight: 1.25, whiteSpace: "nowrap" }}
      />
    </Card>
  );
  return tooltip ? <Tooltip title={tooltip}>{content}</Tooltip> : content;
}

export default function SmartDataHubOverviewPage() {
  const [overview, setOverview] = useState(DEFAULT_OVERVIEW);
  const [deviceStats, setDeviceStats] = useState([]);
  const [assets, setAssets] = useState([]);
  const [assetTotal, setAssetTotal] = useState(0);
  const [files, setFiles] = useState([]);
  const [selectedDevice, setSelectedDevice] = useState(null);
  const [selectedAsset, setSelectedAsset] = useState(null);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [dashboardLoading, setDashboardLoading] = useState(false);
  const [assetsLoading, setAssetsLoading] = useState(false);
  const [filesLoading, setFilesLoading] = useState(false);
  const [loadFailed, setLoadFailed] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");

  const selectedDeviceId = selectedDevice?.device_id || "";

  const deviceColumns = useMemo(
    () => [
      {
        title: "设备",
        dataIndex: "device_id",
        key: "device_id",
        render: (value) => <Text strong>{value || "--"}</Text>
      },
      { title: "资产", dataIndex: "asset_count", key: "asset_count", width: 100 },
      { title: "文件", dataIndex: "file_count", key: "file_count", width: 100 },
      {
        title: "存储",
        dataIndex: "total_size",
        key: "total_size",
        width: 130,
        render: (value) => formatBytes(value)
      },
      { title: "Collector", dataIndex: "collector_count", key: "collector_count", width: 120 },
      { title: "数据类型", dataIndex: "data_type_count", key: "data_type_count", width: 120 },
      {
        title: "最近入库",
        dataIndex: "latest_ingested_at",
        key: "latest_ingested_at",
        width: 180,
        render: (value) => <Tooltip title={value || "--"}>{formatDateTime(value)}</Tooltip>
      }
    ],
    []
  );

  const assetColumns = useMemo(
    () => [
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
      { title: "Collector", dataIndex: "collector_id", key: "collector_id", width: 160 },
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
        render: (value) => <Tooltip title={value || "--"}>{formatDateTime(value)}</Tooltip>
      }
    ],
    []
  );

  const fileColumns = useMemo(
    () => [
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
    ],
    []
  );

  async function loadDashboard() {
    setDashboardLoading(true);
    try {
      const data = await fetchDataDeviceStats();
      setOverview({ ...DEFAULT_OVERVIEW, ...data.overall });
      setDeviceStats(normalizeDeviceStats(data.items));
      setLoadFailed(false);
      setErrorMessage("");
    } catch (error) {
      console.error("加载 SmartDataHub 设备统计失败", error);
      setOverview(DEFAULT_OVERVIEW);
      setDeviceStats([]);
      setLoadFailed(true);
      setErrorMessage(buildRequestErrorMessage(error));
    } finally {
      setDashboardLoading(false);
    }
  }

  async function loadAssets(deviceId) {
    if (!deviceId) {
      setAssets([]);
      setAssetTotal(0);
      return;
    }
    setAssetsLoading(true);
    try {
      const response = await fetchDataAssets({
        device_id: deviceId,
        limit: DEFAULT_ASSET_LIMIT
      });
      setAssets(normalizeAssets(response.items));
      setAssetTotal(response.total);
      setLoadFailed(false);
      setErrorMessage("");
    } catch (error) {
      console.error("加载 SmartDataHub 资产失败", error);
      setAssets([]);
      setAssetTotal(0);
      setLoadFailed(true);
      setErrorMessage(buildRequestErrorMessage(error));
    } finally {
      setAssetsLoading(false);
    }
  }

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

  async function refreshAll() {
    await loadDashboard();
    if (selectedDeviceId) {
      await loadAssets(selectedDeviceId);
    }
  }

  useEffect(() => {
    loadDashboard();
  }, []);

  return (
    <section className="page-section">
      <PageToolbar />
      {loadFailed && errorMessage ? (
        <Alert type="error" showIcon message="数据加载失败" description={errorMessage} style={{ marginBottom: 16 }} />
      ) : null}

      <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
        <Col xs={24} sm={12} lg={4}>
          <OverviewStatCard title="接入设备" value={overview.device_count} loading={dashboardLoading} />
        </Col>
        <Col xs={24} sm={12} lg={4}>
          <OverviewStatCard title="资产" value={overview.asset_count} icon={<DatabaseOutlined />} loading={dashboardLoading} />
        </Col>
        <Col xs={24} sm={12} lg={4}>
          <OverviewStatCard title="文件" value={overview.file_count} icon={<FileSearchOutlined />} loading={dashboardLoading} />
        </Col>
        <Col xs={24} sm={12} lg={4}>
          <OverviewStatCard title="存储" value={formatBytes(overview.total_size)} icon={<HddOutlined />} loading={dashboardLoading} />
        </Col>
        <Col xs={24} sm={12} lg={4}>
          <OverviewStatCard title="Collector" value={overview.collector_count} icon={<CloudServerOutlined />} loading={dashboardLoading} />
        </Col>
        <Col xs={24} sm={12} lg={4}>
          <OverviewStatCard
            title="最近入库"
            value={formatDateTime(overview.latest_ingested_at)}
            loading={dashboardLoading}
            tooltip={overview.latest_ingested_at || "--"}
          />
        </Col>
      </Row>

      <Card
        title="设备数据统计"
        extra={<Button icon={<ReloadOutlined />} onClick={refreshAll}>刷新</Button>}
        style={{ marginBottom: 16 }}
      >
        <Table
          rowKey="row_key"
          columns={deviceColumns}
          dataSource={deviceStats}
          loading={dashboardLoading}
          pagination={{ pageSize: 8, showSizeChanger: false }}
          scroll={{ x: 900 }}
          locale={{ emptyText: <Empty description="暂无 SmartDataHub 设备数据" /> }}
          onRow={(record) => ({
            onClick: () => {
              setSelectedDevice(record);
              loadAssets(record.device_id);
            },
            style: { cursor: "pointer" }
          })}
          rowClassName={(record) => (record.device_id === selectedDeviceId ? "ant-table-row-selected" : "")}
        />
      </Card>

      <Card title={selectedDeviceId ? `${selectedDeviceId} 数据资产` : "设备数据资产"}>
        <Text type="secondary" style={{ display: "block", marginBottom: 12 }}>
          {selectedDeviceId ? `当前设备 ${assetTotal} 条资产，表格展示最近 ${DEFAULT_ASSET_LIMIT} 条。` : "选择设备后显示资产。"}
        </Text>
        <Table
          rowKey="row_key"
          columns={assetColumns}
          dataSource={assets}
          loading={assetsLoading}
          pagination={{ pageSize: 10, showSizeChanger: false }}
          scroll={{ x: 1000 }}
          locale={{ emptyText: <Empty description={selectedDeviceId ? "暂无该设备数据资产" : "暂无已选设备"} /> }}
          onRow={(record) => ({
            onClick: () => openAssetDetail(record),
            style: { cursor: "pointer" }
          })}
        />
      </Card>

      <Drawer title={selectedAsset?.display_name || "数据资产详情"} open={drawerOpen} width={860} onClose={() => setDrawerOpen(false)} destroyOnClose>
        {selectedAsset ? (
          <Space direction="vertical" size={16} style={{ width: "100%" }}>
            <Descriptions bordered column={2} size="small" title="来源">
              <Descriptions.Item label="设备">{selectedAsset.device_id || "--"}</Descriptions.Item>
              <Descriptions.Item label="Collector">{selectedAsset.collector_id || "--"}</Descriptions.Item>
            </Descriptions>
            <Descriptions bordered column={2} size="small" title="资产信息">
              <Descriptions.Item label="资产 ID" span={2}>{selectedAsset.asset_id}</Descriptions.Item>
              <Descriptions.Item label="资产组">{selectedAsset.asset_group_id || "--"}</Descriptions.Item>
              <Descriptions.Item label="数据类型">{selectedAsset.data_type || "--"}</Descriptions.Item>
              <Descriptions.Item label="文件数">{selectedAsset.file_count}</Descriptions.Item>
              <Descriptions.Item label="总大小">{formatBytes(selectedAsset.total_size)}</Descriptions.Item>
              <Descriptions.Item label="创建时间">{formatDateTime(selectedAsset.created_at)}</Descriptions.Item>
              <Descriptions.Item label="入库时间">{formatDateTime(selectedAsset.ingested_at)}</Descriptions.Item>
            </Descriptions>
            <Descriptions bordered column={1} size="small" title="存储">
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
                scroll={{ x: 820 }}
                locale={{ emptyText: <Empty description="暂无文件明细" /> }}
              />
            </Card>
          </Space>
        ) : null}
      </Drawer>
    </section>
  );
}
