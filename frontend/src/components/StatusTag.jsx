import React from "react";
import { Tag } from "antd";

const STATUS_COLOR_MAP = {
  accepted: "processing",
  blocked: "warning",
  queued: "warning",
  rejected: "error",
  running: "processing",
  success: "success",
  failed: "error",
  error: "error",
  pending: "warning",
  online: "success",
  info: "blue",
  idle: "default",
  offline: "error",
  unknown: "default",
  disabled: "default",
  warning: "warning",
  draft: "blue",
  published: "success"
};

const STATUS_LABEL_MAP = {
  accepted: "已接收",
  blocked: "阻塞",
  queued: "排队中",
  rejected: "已拒绝",
  running: "运行中",
  success: "成功",
  failed: "失败",
  error: "错误",
  pending: "等待中",
  online: "在线",
  info: "信息",
  idle: "空闲",
  offline: "离线",
  unknown: "未知",
  disabled: "未启用",
  warning: "告警",
  draft: "草稿",
  published: "已发布"
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
