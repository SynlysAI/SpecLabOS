import React from "react";

/**
 * 系统日志占位页。
 *
 * Returns:
 *     展示系统日志入口的占位内容。
 */
export default function SystemLogsPage() {
  return (
    <section className="page-section">
      <h1 className="page-heading">系统日志</h1>
      <p className="page-subheading">
        这里将用于查看系统审计日志、服务事件与运行异常明细。
      </p>
    </section>
  );
}
