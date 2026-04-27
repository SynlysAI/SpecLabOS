import React from "react";
import { Tag } from "antd";

const STATUS_COLOR_MAP = {
  running: "processing",
  online: "success",
  idle: "default",
  offline: "error",
  warning: "warning",
  draft: "blue"
};

const STATUS_LABEL_MAP = {
  running: "运行中",
  online: "在线",
  idle: "空闲",
  offline: "离线",
  warning: "告警",
  draft: "草稿"
};

/**
 * 状态标签组件。
 *
 * Args:
 *     status: 状态编码。
 *     label: 自定义状态文案。
 *
 * Returns:
 *     统一风格的状态标签。
 */
export default function StatusTag({ status, label }) {
  const normalizedStatus = status || "idle";

  return (
    <Tag color={STATUS_COLOR_MAP[normalizedStatus] || "default"} bordered={false}>
      {label || STATUS_LABEL_MAP[normalizedStatus] || normalizedStatus}
    </Tag>
  );
}
