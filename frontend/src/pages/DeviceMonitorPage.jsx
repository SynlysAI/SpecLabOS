import React, { useEffect, useState } from "react";
import { Alert, Button, Card, Col, Image, Row, Space, Spin, Table, Tag } from "antd";
import { ReloadOutlined } from "@ant-design/icons";

import DeviceDetailDrawer from "../components/DeviceDetailDrawer";
import PageToolbar from "../components/PageToolbar";
import StatusTag from "../components/StatusTag";
import { fetchDevices, resolveDeviceImageUrl } from "../services/deviceApi";
import { formatDeviceAccessMode } from "../utils/deviceDisplay";

const columns = [
  {
    title: "设备",
    key: "device",
    render: (_, record) => (
      <Space size={12}>
        {record.image_url ? (
          <Image
            src={resolveDeviceImageUrl(record.image_url)}
            alt={record.name}
            width={44}
            height={44}
            style={{ borderRadius: 8, objectFit: "cover" }}
            preview={false}
          />
        ) : null}
        <Space direction="vertical" size={0}>
          <Space size={6}>
            <strong>{record.name}</strong>
            {record.permission === "control" ? (
              <Tag color="green" bordered={false}>可控</Tag>
            ) : (
              <Tag bordered={false}>只读</Tag>
            )}
          </Space>
          <span style={{ color: "#667085", fontSize: 12 }}>{record.device_type}</span>
        </Space>
      </Space>
    )
  },
  {
    title: "分类",
    dataIndex: "category",
    key: "category"
  },
  {
    title: "接入模式",
    dataIndex: "adapter_type",
    key: "adapter_type",
    render: (value) => formatDeviceAccessMode(value)
  },
  {
    title: "状态",
    dataIndex: ["status_snapshot", "state"],
    key: "state",
    render: (value) => <StatusTag status={value} />
  },
  {
    title: "启用",
    dataIndex: "enabled",
    key: "enabled",
    render: (value) => (value ? "是" : "否")
  }
];

/**
 * 规范设备列表数据。
 *
 * Args:
 *     items: 原始设备列表。
 *
 * Returns:
 *     可直接供表格使用的设备列表。
 */
function normalizeDevices(items) {
  return items.map((item, index) => ({
    key: item.key || item.id || `device-${index}`,
    ...item
  }));
}

/**
 * 设备监控页。
 *
 * Returns:
 *     展示设备监控表格、摘要卡片和详情抽屉。
 */
export default function DeviceMonitorPage() {
  const [devices, setDevices] = useState([]);
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [selectedDevice, setSelectedDevice] = useState(null);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [loadError, setLoadError] = useState(false);

  /**
   * 加载设备列表。
   *
   * Returns:
   *     无返回值。
   */
  async function loadDevices({ refreshStatus = false } = {}) {
    const setBusy = refreshStatus ? setRefreshing : setLoading;
    setBusy(true);
    try {
      const items = await fetchDevices({ refreshStatus });
      setDevices(normalizeDevices(items));
      setLoadError(false);
    } catch (error) {
      setLoadError(true);
      if (!devices.length) {
        setDevices([]);
      }
    } finally {
      setBusy(false);
    }
  }

  useEffect(() => {
    loadDevices({ refreshStatus: true });
  }, []);

  /**
   * 打开设备详情。
   *
   * Args:
   *     record: 当前点击的设备记录。
   *
   * Returns:
   *     无返回值。
   */
  function handleOpenDetail(record) {
    setSelectedDevice(record);
    setDrawerOpen(true);
  }

  const onlineCount = devices.filter(
    (item) => ["online", "running", "idle"].includes(item.status_snapshot?.state)
  ).length;
  const warningCount = devices.filter(
    (item) => ["warning", "offline", "error", "failed"].includes(item.status_snapshot?.state)
  ).length;
  const initialLoading = loading && !devices.length;

  return (
    <section className="page-section">
      <PageToolbar />
      {loadError ? (
        <Alert
          type="warning"
          showIcon
          message="设备接口请求失败，已保留当前设备列表；请检查后端服务或稍后刷新。"
          style={{ marginBottom: 16 }}
        />
      ) : null}
      <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
        <Col xs={24} md={8}>
          <Card size="small" title="设备总数" loading={loading && !devices.length}>
            <strong style={{ fontSize: 28 }}>{devices.length}</strong>
          </Card>
        </Col>
        <Col xs={24} md={8}>
          <Card size="small" title="在线设备" loading={loading && !devices.length}>
            <strong style={{ fontSize: 28 }}>{onlineCount}</strong>
          </Card>
        </Col>
        <Col xs={24} md={8}>
          <Card size="small" title="待处理异常" loading={loading && !devices.length}>
            <strong style={{ fontSize: 28 }}>{warningCount}</strong>
          </Card>
        </Col>
      </Row>
      <Card
        title="设备状态列表"
        extra={
          <Space>
            <Button
              icon={<ReloadOutlined />}
              onClick={() => loadDevices({ refreshStatus: true })}
              loading={refreshing}
            >
              刷新状态
            </Button>
          </Space>
        }
      >
        <Spin spinning={initialLoading} tip="正在加载设备状态...">
          <Table
            rowKey="key"
            columns={columns}
            dataSource={devices}
            loading={refreshing}
            pagination={false}
            locale={{ emptyText: loadError ? "设备列表加载失败" : "暂无设备数据" }}
            onRow={(record) => ({
              onClick: () => handleOpenDetail(record),
              style: { cursor: "pointer" }
            })}
          />
        </Spin>
      </Card>
      <DeviceDetailDrawer
        open={drawerOpen}
        device={selectedDevice}
        onClose={() => setDrawerOpen(false)}
      />
    </section>
  );
}
