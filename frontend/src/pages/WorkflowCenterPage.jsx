import React from "react";
import { Tabs } from "antd";
import { useNavigate, useParams } from "react-router-dom";

import SmartAccessTemplatesPage from "./SmartAccessTemplatesPage";
import WorkflowBuilderPage from "./WorkflowBuilderPage";

const WORKFLOW_TABS = [
  {
    key: "local-builder",
    label: "本地编排",
    description: "面向 SpecLabOS 本地注册设备，编排 LocalAdapter 可执行工作流。",
    children: <WorkflowBuilderPage />
  },
  {
    key: "smartaccess-templates",
    label: "SmartAccess 模板",
    description: "管理 SmartAccess 已发布工作流模板，用于后续远程下发执行。",
    children: <SmartAccessTemplatesPage />
  }
];

/**
 * 工作流中心页。
 *
 * Returns:
 *     通过子页签统一承载工作流定义、编排与模板管理能力。
 */
export default function WorkflowCenterPage() {
  const navigate = useNavigate();
  const { tabKey } = useParams();
  const activeKey = WORKFLOW_TABS.some((tab) => tab.key === tabKey)
    ? tabKey
    : WORKFLOW_TABS[0].key;

  /**
   * 切换工作流中心子页签。
   *
   * Args:
   *     nextKey: 目标子页签标识。
   */
  function handleTabChange(nextKey) {
    navigate(`/workflows/${nextKey}`);
  }

  return (
    <section className="page-section">
      <Tabs
        activeKey={activeKey}
        onChange={handleTabChange}
        items={WORKFLOW_TABS.map((tab) => ({
          key: tab.key,
          label: tab.label,
          children: tab.children
        }))}
        destroyInactiveTabPane
      />
    </section>
  );
}
