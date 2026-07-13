import React from "react";
import { Alert, Tabs } from "antd";
import { useNavigate, useParams } from "react-router-dom";

import SmartAccessRunsPage from "./SmartAccessRunsPage";
import WorkflowRunsPage from "./WorkflowRunsPage";

const TASK_TABS = [
  {
    key: "orchestration-runs",
    label: "编排任务",
    description: "查看由 SpecLabOS 工作流编排下发执行的任务记录。",
    children: <WorkflowRunsPage />
  },
  {
    key: "smartaccess-runs",
    label: "SmartAccess 任务",
    description: "查看经 SmartAccess 下发到远程执行端的任务记录。",
    children: <SmartAccessRunsPage />
  }
];

/**
 * 任务中心页。
 *
 * Returns:
 *     通过子页签统一承载编排任务和 SmartAccess 远程任务运行记录。
 */
export default function TaskCenterPage() {
  const navigate = useNavigate();
  const { tabKey } = useParams();
  const activeKey = TASK_TABS.some((tab) => tab.key === tabKey)
    ? tabKey
    : TASK_TABS[0].key;
  const activeTab = TASK_TABS.find((tab) => tab.key === activeKey);

  /**
   * 切换任务中心子页签。
   *
   * Args:
   *     nextKey: 目标子页签标识。
   */
  function handleTabChange(nextKey) {
    navigate(`/tasks/${nextKey}`);
  }

  return (
    <section className="page-section">
      <Alert
        type="info"
        showIcon
        message={activeTab?.description}
        style={{ marginBottom: 16 }}
      />
      <Tabs
        activeKey={activeKey}
        onChange={handleTabChange}
        items={TASK_TABS.map((tab) => ({
          key: tab.key,
          label: tab.label,
          children: tab.children
        }))}
        destroyInactiveTabPane
      />
    </section>
  );
}
