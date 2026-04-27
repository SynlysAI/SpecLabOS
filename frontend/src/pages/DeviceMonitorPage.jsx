import React from "react";

/**
 * 设备监控总览占位页。
 *
 * Returns:
 *     展示设备监控入口的占位内容。
 */
export default function DeviceMonitorPage() {
  return (
    <section className="page-section">
      <h1 className="page-heading">设备监控总览</h1>
      <p className="page-subheading">
        这里将汇总实验设备状态、在线告警与实时任务概览。
      </p>
    </section>
  );
}
