import React from "react";

/**
 * 工作流运行记录占位页。
 *
 * Returns:
 *     展示运行记录入口的占位内容。
 */
export default function WorkflowRunsPage() {
  return (
    <section className="page-section">
      <h1 className="page-heading">运行记录</h1>
      <p className="page-subheading">
        这里将展示流程执行历史、运行状态与异常重试结果。
      </p>
    </section>
  );
}
