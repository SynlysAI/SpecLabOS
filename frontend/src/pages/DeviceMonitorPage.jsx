import React, { useEffect, useState } from "react";
import { Alert, Button, Card, Col, Image, Row, Space, Table } from "antd";
import { ReloadOutlined } from "@ant-design/icons";

import DeviceDetailDrawer from "../components/DeviceDetailDrawer";
import PageToolbar from "../components/PageToolbar";
import StatusTag from "../components/StatusTag";
import { fetchDevices, resolveDeviceImageUrl } from "../services/deviceApi";

const FALLBACK_DEVICES = [
  {
    key: "nmr_2278",
    name: "nmr_2278",
    category: "核磁共振仪",
    device_type: "NMRSpectrometer",
    image_url: "/api/device-images/NMRSpectrometer",
    enabled: true,
    location: "A-203",
    status_snapshot: {
      state: "online",
      updated_at: "2026-04-27 17:40"
    }
  },
  {
    key: "gpc_2278",
    name: "gpc_2278",
    category: "凝胶渗透色谱仪",
    device_type: "GPCAnalyzer",
    image_url: "/api/device-images/GPCAnalyzer",
    enabled: true,
    location: "A-105",
    status_snapshot: {
      state: "running",
      updated_at: "2026-04-27 17:36"
    }
  },
  {
    key: "resin_2278",
    name: "resin_2278",
    category: "树脂工作站",
    device_type: "ResinWorkstation",
    image_url: "/api/device-images/ResinWorkstation",
    enabled: false,
    location: "B-201",
    status_snapshot: {
      state: "offline",
      updated_at: "2026-04-27 16:58"
    }
  }
];

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
          <strong>{record.name}</strong>
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
  const [devices, setDevices] = useState(normalizeDevices(FALLBACK_DEVICES));
  const [loading, setLoading] = useState(false);
  const [selectedDevice, setSelectedDevice] = useState(null);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [usingFallbackData, setUsingFallbackData] = useState(true);

  /**
   * 加载设备列表。
   *
   * Returns:
   *     无返回值。
   */
  async function loadDevices() {
    setLoading(true);
    try {
      const items = await fetchDevices();
      setDevices(normalizeDevices(items));
      setUsingFallbackData(false);
    } catch (error) {
      setDevices(normalizeDevices(FALLBACK_DEVICES));
      setUsingFallbackData(true);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadDevices();
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
    (item) => item.status_snapshot?.state === "online" || item.status_snapshot?.state === "running"
  ).length;
  const warningCount = devices.filter(
    (item) => item.status_snapshot?.state === "warning" || item.status_snapshot?.state === "offline"
  ).length;

  return (
    <section className="page-section">
      <PageToolbar
        extra={
          <Button icon={<ReloadOutlined />} onClick={loadDevices} loading={loading}>
            刷新设备
          </Button>
        }
      />
      {usingFallbackData ? (
        <Alert
          type="warning"
          showIcon
          message="当前接口不可用，页面展示的是示例设备数据。"
          style={{ marginBottom: 16 }}
        />
      ) : null}
      <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
        <Col xs={24} md={8}>
          <Card size="small" title="设备总数">
            <strong style={{ fontSize: 28 }}>{devices.length}</strong>
          </Card>
        </Col>
        <Col xs={24} md={8}>
          <Card size="small" title="在线设备">
            <strong style={{ fontSize: 28 }}>{onlineCount}</strong>
          </Card>
        </Col>
        <Col xs={24} md={8}>
          <Card size="small" title="待处理异常">
            <strong style={{ fontSize: 28 }}>{warningCount}</strong>
          </Card>
        </Col>
      </Row>
      <Card
        title="设备状态列表"
        extra={
          !usingFallbackData ? (
            <Space>
              <StatusTag status="online" label="实时更新" />
            </Space>
          ) : null
        }
      >
        <Table
          rowKey="key"
          columns={columns}
          dataSource={devices}
          loading={loading}
          pagination={false}
          onRow={(record) => ({
            onClick: () => handleOpenDetail(record),
            style: { cursor: "pointer" }
          })}
        />
      </Card>
      <DeviceDetailDrawer
        open={drawerOpen}
        device={selectedDevice}
        onClose={() => setDrawerOpen(false)}
      />
    </section>
  );
}
