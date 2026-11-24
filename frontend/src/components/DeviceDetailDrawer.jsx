import React from "react";
import { Button, Descriptions, Drawer, Empty, Image, Popconfirm, Space } from "antd";

import StatusTag from "./StatusTag";
import { resolveDeviceImageUrl } from "../services/deviceApi";
import { formatDeviceAccessMode } from "../utils/deviceDisplay";

/**
 * 设备详情抽屉组件。
 *
 * Args:
 *     open: 抽屉是否打开。
 *     device: 当前选中的设备。
 *     onClose: 关闭回调。
 *     onCancelAccess: 取消 SmartAccess 设备接入的回调。
 *
 * Returns:
 *     展示设备基础信息与状态摘要的抽屉。
 */
export default function DeviceDetailDrawer({ open, device, onClose, onCancelAccess }) {
  return (
    <Drawer
      title={device ? `${device.name} 详情` : "设备详情"}
      width={420}
      open={open}
      onClose={onClose}
    >
      {device ? (
        <Space direction="vertical" size={16} style={{ width: "100%" }}>
          {device.image_url ? (
            <Image
              src={resolveDeviceImageUrl(device.image_url)}
              alt={device.name}
              style={{ width: "100%", borderRadius: 12 }}
            />
          ) : null}
          <Descriptions column={1} bordered size="small" labelStyle={{ width: 96 }}>
            <Descriptions.Item label="设备名称">{device.name}</Descriptions.Item>
            <Descriptions.Item label="设备分类">{device.category}</Descriptions.Item>
            <Descriptions.Item label="设备类型">{device.device_type}</Descriptions.Item>
            <Descriptions.Item label="接入模式">
              {formatDeviceAccessMode(device.adapter_type)}
            </Descriptions.Item>
            {device.published_by ? (
              <Descriptions.Item label="发布人">{device.published_by}</Descriptions.Item>
            ) : null}
            <Descriptions.Item label="当前状态">
              <StatusTag status={device.status_snapshot?.state} />
            </Descriptions.Item>
            <Descriptions.Item label="启用状态">
              {device.enabled ? "已启用" : "未启用"}
            </Descriptions.Item>
            <Descriptions.Item label="最近心跳">
              {device.status_snapshot?.updated_at || "暂无"}
            </Descriptions.Item>
            <Descriptions.Item label="位置">
              {device.location || "未登记"}
            </Descriptions.Item>
          </Descriptions>
          {device.adapter_type === "smartaccess" && device.permission === "control" ? (
            <Popconfirm
              title="确认取消接入？"
              description="设备会从监控页移除，已发布的流程也会下线。"
              okText="取消接入"
              cancelText="保留"
              okButtonProps={{ danger: true }}
              onConfirm={() => onCancelAccess?.(device)}
            >
              <Button danger>取消接入</Button>
            </Popconfirm>
          ) : null}
        </Space>
      ) : (
        <Empty description="请选择设备查看详情" />
      )}
    </Drawer>
  );
}
