import React from "react";
import { Tabs } from "antd";
import { useNavigate, useParams } from "react-router-dom";

import SmartAccessRunsPage from "./SmartAccessRunsPage";
import WorkflowRunsPage from "./WorkflowRunsPage";

const TASK_TABS = [
  {
    key: "orchestration-runs",
    label: "编排任务",
    children: <WorkflowRunsPage />
  },
  {
    key: "smartaccess-runs",
    label: "SmartAccess 任务",
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
