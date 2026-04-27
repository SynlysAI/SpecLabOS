import React from "react";
import { Descriptions, Drawer, Empty, Image, Space } from "antd";

import StatusTag from "./StatusTag";
import { resolveDeviceImageUrl } from "../services/deviceApi";

/**
 * 设备详情抽屉组件。
 *
 * Args:
 *     open: 抽屉是否打开。
 *     device: 当前选中的设备。
 *     onClose: 关闭回调。
 *
 * Returns:
 *     展示设备基础信息与状态摘要的抽屉。
 */
export default function DeviceDetailDrawer({ open, device, onClose }) {
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
          <Descriptions column={1} bordered size="small">
            <Descriptions.Item label="设备名称">{device.name}</Descriptions.Item>
            <Descriptions.Item label="设备分类">{device.category}</Descriptions.Item>
            <Descriptions.Item label="设备类型">{device.device_type}</Descriptions.Item>
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
        </Space>
      ) : (
        <Empty description="请选择设备查看详情" />
      )}
    </Drawer>
  );
}
