import React, { useEffect, useMemo, useState } from "react";
import {
  Alert,
  Button,
  Card,
  Col,
  Empty,
  Input,
  List,
  message,
  Row,
  Space,
  Spin,
  Tabs,
  Tag,
  Typography,
} from "antd";
import {
  ReloadOutlined,
  SearchOutlined,
  UserOutlined,
  ApiOutlined,
} from "@ant-design/icons";

import PageToolbar from "../../components/PageToolbar";
import {
  getDeviceUsers,
  getUserDevices,
  listUsers,
  replaceDeviceUsers,
  replaceUserDevices,
} from "../../services/adminApi";
import { fetchDevices } from "../../services/deviceApi";

const { Text, Title } = Typography;

/**
 * 用户卡片(左侧用户列表项)。
 */
function UserCard({ user, selected, onClick }) {
  return (
    <List.Item
      onClick={onClick}
      style={{
        cursor: "pointer",
        padding: "12px 16px",
        background: selected ? "#e6f4ff" : "transparent",
        borderLeft: selected ? "3px solid #1677ff" : "3px solid transparent",
        transition: "all .15s",
      }}
    >
      <Space direction="vertical" size={0} style={{ width: "100%" }}>
        <Space>
          <UserOutlined />
          <Text strong>{user.username}</Text>
          {user.role === "admin" ? (
            <Tag color="gold">管理员</Tag>
          ) : (
            <Tag color="blue">普通用户</Tag>
          )}
        </Space>
        <Text type="secondary" style={{ fontSize: 12 }}>
          {user.organization || "—"}
        </Text>
      </Space>
    </List.Item>
  );
}

/**
 * 设备卡片(左侧设备列表项)。
 */
function DeviceCard({ device, selected, onClick }) {
  return (
    <List.Item
      onClick={onClick}
      style={{
        cursor: "pointer",
        padding: "12px 16px",
        background: selected ? "#e6f4ff" : "transparent",
        borderLeft: selected ? "3px solid #1677ff" : "3px solid transparent",
        transition: "all .15s",
      }}
    >
      <Space direction="vertical" size={0} style={{ width: "100%" }}>
        <Space>
          <ApiOutlined />
          <Text strong>{device.name}</Text>
        </Space>
        <Text type="secondary" style={{ fontSize: 12 }}>
          {device.device_type} · {device.category}
        </Text>
      </Space>
    </List.Item>
  );
}

/**
 * 权限管理 - 按用户管 Tab。
 */
function ByUserPane() {
  const [users, setUsers] = useState([]);
  const [devices, setDevices] = useState([]);
  const [selectedUser, setSelectedUser] = useState(null);
  const [grantedKeys, setGrantedKeys] = useState([]);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [searchKeyword, setSearchKeyword] = useState("");
  const [messageApi, contextHolder] = message.useMessage();

  /**
   * 加载用户与设备列表。
   */
  async function loadAll() {
    setLoading(true);
    try {
      const [userList, deviceList] = await Promise.all([
        listUsers(),
        fetchDevices(),
      ]);
      setUsers(Array.isArray(userList) ? userList : []);
      setDevices(deviceList);
      if (userList.length && !selectedUser) {
        setSelectedUser(userList[0]);
      }
    } catch (error) {
      messageApi.error("加载用户/设备列表失败");
    } finally {
      setLoading(false);
    }
  }

  /**
   * 加载指定用户的当前可控设备。
   *
   * Args:
   *     userId: 用户唯一 ID。
   */
  async function loadUserDevices(userId) {
    if (!userId) {
      setGrantedKeys([]);
      return;
    }
    try {
      const data = await getUserDevices(userId);
      setGrantedKeys(data.device_keys || []);
    } catch (error) {
      messageApi.error("加载用户权限失败");
      setGrantedKeys([]);
    }
  }

  useEffect(() => {
    loadAll();
  }, []);

  useEffect(() => {
    if (selectedUser) {
      loadUserDevices(selectedUser.user_id);
    } else {
      setGrantedKeys([]);
    }
  }, [selectedUser?.user_id]);

  const filteredUsers = useMemo(() => {
    const keyword = searchKeyword.trim().toLowerCase();
    if (!keyword) return users;
    return users.filter(
      (u) =>
        (u.username || "").toLowerCase().includes(keyword) ||
        (u.organization || "").toLowerCase().includes(keyword),
    );
  }, [users, searchKeyword]);

  /**
   * 切换某设备的授权。
   *
   * Args:
   *     deviceKey: 设备标识。
   *     nextGranted: 是否授权。
   */
  async function toggleDevice(deviceKey, nextGranted) {
    if (!selectedUser) return;
    const nextKeys = nextGranted
      ? Array.from(new Set([...grantedKeys, deviceKey]))
      : grantedKeys.filter((k) => k !== deviceKey);
    setGrantedKeys(nextKeys);
    setSaving(true);
    try {
      await replaceUserDevices(selectedUser.user_id, nextKeys);
      messageApi.success(nextGranted ? "已授权" : "已撤销");
    } catch (error) {
      messageApi.error("权限更新失败,正在回滚");
      loadUserDevices(selectedUser.user_id);
    } finally {
      setSaving(false);
    }
  }

  /**
   * 一键全选/全清。
   *
   * Args:
   *     grantAll: 是否全部授权。
   */
  async function bulkToggle(grantAll) {
    if (!selectedUser) return;
    const nextKeys = grantAll ? devices.map((d) => d.key) : [];
    setGrantedKeys(nextKeys);
    setSaving(true);
    try {
      await replaceUserDevices(selectedUser.user_id, nextKeys);
      messageApi.success(grantAll ? "已授权全部设备" : "已撤销全部设备");
    } catch (error) {
      messageApi.error("批量更新失败");
      loadUserDevices(selectedUser.user_id);
    } finally {
      setSaving(false);
    }
  }

  return (
    <Row gutter={[16, 16]} style={{ minHeight: 480 }}>
      {contextHolder}
      <Col xs={24} md={8}>
        <Card
          title="用户列表"
          size="small"
          extra={
            <Button
              icon={<ReloadOutlined />}
              onClick={loadAll}
              loading={loading}
              type="text"
              size="small"
            />
          }
        >
          <Input
            allowClear
            prefix={<SearchOutlined />}
            placeholder="搜索用户名/单位"
            value={searchKeyword}
            onChange={(e) => setSearchKeyword(e.target.value)}
            style={{ marginBottom: 12 }}
          />
          <Spin spinning={loading}>
            <List
              dataSource={filteredUsers}
              locale={{ emptyText: <Empty description="暂无用户" /> }}
              renderItem={(user) => (
                <UserCard
                  key={user.user_id}
                  user={user}
                  selected={selectedUser?.user_id === user.user_id}
                  onClick={() => setSelectedUser(user)}
                />
              )}
              style={{ maxHeight: 540, overflow: "auto" }}
            />
          </Spin>
        </Card>
      </Col>
      <Col xs={24} md={16}>
        <Card
          title={
            selectedUser
              ? `${selectedUser.username} 的可控设备`
              : "请选择用户"
          }
          size="small"
          extra={
            selectedUser && selectedUser.role !== "admin" ? (
              <Space>
                <Button size="small" onClick={() => bulkToggle(true)}>
                  全部授权
                </Button>
                <Button size="small" onClick={() => bulkToggle(false)} danger>
                  撤销全部
                </Button>
              </Space>
            ) : null
          }
        >
          {selectedUser?.role === "admin" ? (
            <Alert
              type="info"
              showIcon
              message="管理员默认拥有全部设备的控制权限,无需单独授权。"
            />
          ) : selectedUser ? (
            <Spin spinning={saving}>
              <List
                dataSource={devices}
                locale={{ emptyText: <Empty description="暂无设备" /> }}
                renderItem={(device) => {
                  const granted = grantedKeys.includes(device.key);
                  return (
                    <List.Item
                      actions={[
                        <Button
                          key="toggle"
                          size="small"
                          type={granted ? "primary" : "default"}
                          danger={granted}
                          onClick={() => toggleDevice(device.key, !granted)}
                        >
                          {granted ? "撤销控制权" : "授予控制权"}
                        </Button>,
                      ]}
                    >
                      <List.Item.Meta
                        avatar={<ApiOutlined style={{ fontSize: 20 }} />}
                        title={
                          <Space>
                            <Text strong>{device.name}</Text>
                            {granted ? (
                              <Tag color="green">可控</Tag>
                            ) : (
                              <Tag>只读</Tag>
                            )}
                          </Space>
                        }
                        description={`${device.device_type} · ${
                          device.category || ""
                        } · ${device.location || ""}`}
                      />
                    </List.Item>
                  );
                }}
                style={{ maxHeight: 540, overflow: "auto" }}
              />
            </Spin>
          ) : (
            <Empty description="从左侧选择一个用户开始配置" />
          )}
        </Card>
      </Col>
    </Row>
  );
}

/**
 * 权限管理 - 按设备管 Tab。
 */
function ByDevicePane() {
  const [devices, setDevices] = useState([]);
  const [users, setUsers] = useState([]);
  const [selectedDevice, setSelectedDevice] = useState(null);
  const [grantedUserIds, setGrantedUserIds] = useState([]);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [searchKeyword, setSearchKeyword] = useState("");
  const [messageApi, contextHolder] = message.useMessage();

  async function loadAll() {
    setLoading(true);
    try {
      const [deviceList, userList] = await Promise.all([
        fetchDevices(),
        listUsers(),
      ]);
      setDevices(deviceList);
      setUsers(Array.isArray(userList) ? userList : []);
      if (deviceList.length && !selectedDevice) {
        setSelectedDevice(deviceList[0]);
      }
    } catch (error) {
      messageApi.error("加载设备/用户列表失败");
    } finally {
      setLoading(false);
    }
  }

  async function loadDeviceUsers(deviceKey) {
    if (!deviceKey) {
      setGrantedUserIds([]);
      return;
    }
    try {
      const data = await getDeviceUsers(deviceKey);
      setGrantedUserIds(data.user_ids || []);
    } catch (error) {
      messageApi.error("加载设备授权失败");
      setGrantedUserIds([]);
    }
  }

  useEffect(() => {
    loadAll();
  }, []);

  useEffect(() => {
    if (selectedDevice) {
      loadDeviceUsers(selectedDevice.key);
    } else {
      setGrantedUserIds([]);
    }
  }, [selectedDevice?.key]);

  const filteredDevices = useMemo(() => {
    const keyword = searchKeyword.trim().toLowerCase();
    if (!keyword) return devices;
    return devices.filter(
      (d) =>
        (d.name || "").toLowerCase().includes(keyword) ||
        (d.device_type || "").toLowerCase().includes(keyword),
    );
  }, [devices, searchKeyword]);

  /**
   * 切换某用户的授权。
   */
  async function toggleUser(userId, nextGranted) {
    if (!selectedDevice) return;
    const nextIds = nextGranted
      ? Array.from(new Set([...grantedUserIds, userId]))
      : grantedUserIds.filter((id) => id !== userId);
    setGrantedUserIds(nextIds);
    setSaving(true);
    try {
      await replaceDeviceUsers(selectedDevice.key, nextIds);
      messageApi.success(nextGranted ? "已授权" : "已撤销");
    } catch (error) {
      messageApi.error("权限更新失败,正在回滚");
      loadDeviceUsers(selectedDevice.key);
    } finally {
      setSaving(false);
    }
  }

  return (
    <Row gutter={[16, 16]} style={{ minHeight: 480 }}>
      {contextHolder}
      <Col xs={24} md={8}>
        <Card
          title="设备列表"
          size="small"
          extra={
            <Button
              icon={<ReloadOutlined />}
              onClick={loadAll}
              loading={loading}
              type="text"
              size="small"
            />
          }
        >
          <Input
            allowClear
            prefix={<SearchOutlined />}
            placeholder="搜索设备名/类型"
            value={searchKeyword}
            onChange={(e) => setSearchKeyword(e.target.value)}
            style={{ marginBottom: 12 }}
          />
          <Spin spinning={loading}>
            <List
              dataSource={filteredDevices}
              locale={{ emptyText: <Empty description="暂无设备" /> }}
              renderItem={(device) => (
                <DeviceCard
                  key={device.key}
                  device={device}
                  selected={selectedDevice?.key === device.key}
                  onClick={() => setSelectedDevice(device)}
                />
              )}
              style={{ maxHeight: 540, overflow: "auto" }}
            />
          </Spin>
        </Card>
      </Col>
      <Col xs={24} md={16}>
        <Card
          title={
            selectedDevice
              ? `${selectedDevice.name} 的授权用户`
              : "请选择设备"
          }
          size="small"
        >
          {selectedDevice ? (
            <Spin spinning={saving}>
              <List
                dataSource={users}
                locale={{ emptyText: <Empty description="暂无用户" /> }}
                renderItem={(user) => {
                  const granted = grantedUserIds.includes(user.user_id);
                  const isAdmin = user.role === "admin";
                  return (
                    <List.Item
                      actions={[
                        isAdmin ? (
                          <Tag key="admin" color="gold">
                            管理员默认可控
                          </Tag>
                        ) : (
                          <Button
                            key="toggle"
                            size="small"
                            type={granted ? "primary" : "default"}
                            danger={granted}
                            onClick={() => toggleUser(user.user_id, !granted)}
                          >
                            {granted ? "撤销授权" : "授予控制权"}
                          </Button>
                        ),
                      ]}
                    >
                      <List.Item.Meta
                        avatar={<UserOutlined style={{ fontSize: 20 }} />}
                        title={
                          <Space>
                            <Text strong>{user.username}</Text>
                            {granted ? (
                              <Tag color="green">已授权</Tag>
                            ) : null}
                            {isAdmin ? (
                              <Tag color="gold">管理员</Tag>
                            ) : (
                              <Tag color="blue">普通用户</Tag>
                            )}
                          </Space>
                        }
                        description={user.organization || "—"}
                      />
                    </List.Item>
                  );
                }}
                style={{ maxHeight: 540, overflow: "auto" }}
              />
            </Spin>
          ) : (
            <Empty description="从左侧选择一台设备开始配置" />
          )}
        </Card>
      </Col>
    </Row>
  );
}

/**
 * 权限管理页(双 Tab:按用户管 / 按设备管)。
 *
 * Returns:
 *     管理员可在此页配置用户的设备控制权限。
 */
export default function DevicePermissionsPage() {
  return (
    <section className="page-section">
      <PageToolbar />
      <Title level={5} style={{ marginBottom: 16 }}>
        设备权限管理
      </Title>
      <Text type="secondary" style={{ display: "block", marginBottom: 16 }}>
        管理员可在此配置每个用户可控制的设备范围。所有登录用户默认拥有设备只读权限,需要显式授权才能进行设备控制、工作流提交等操作。
      </Text>
      <Card bordered={false}>
        <Tabs
          defaultActiveKey="by-user"
          items={[
            {
              key: "by-user",
              label: "按用户管",
              children: <ByUserPane />,
            },
            {
              key: "by-device",
              label: "按设备管",
              children: <ByDevicePane />,
            },
          ]}
        />
      </Card>
    </section>
  );
}
