import React, { useMemo, useState } from "react";
import { Button, Input, Modal, Space, Tooltip, message } from "antd";

import { AUTH_TOKEN_KEY } from "../services/http";
import { useAuth } from "../auth/AuthContext";

const AI4MS_API_BASE = String(
  import.meta.env.VITE_AI4MS_API_URL || "https://ai4ms.xmuzc.com"
).replace(/\/+$/, "");
const AI4MS_FEEDBACK_URL = `${AI4MS_API_BASE}/api/v1/feedback`;

/* 平台标识（与 AI4MS 后端 FEEDBACK_PLATFORMS 对应）。 */
const FEEDBACK_PLATFORM = "speclabos";

const FEEDBACK_TYPES = [
  { value: "bug", label: "功能异常" },
  { value: "ux", label: "体验问题" },
  { value: "idea", label: "功能建议" },
  { value: "other", label: "其他" }
];
const MAX_CONTENT_LENGTH = 500;

/** 气泡 + 感叹号图标（与其它子平台保持一致的视觉语义）。 */
function FeedbackIcon() {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      width="14"
      height="14"
    >
      <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
      <line x1="12" y1="7" x2="12" y2="12" />
      <line x1="12" y1="15" x2="12.01" y2="15" />
    </svg>
  );
}

const chipStyle = (active) => ({
  fontSize: 12,
  padding: "5px 14px",
  borderRadius: 999,
  cursor: "pointer",
  border: `1px solid ${active ? "#91caff" : "#e4e9f1"}`,
  background: active ? "#e6f4ff" : "#f4f6f9",
  color: active ? "#1677ff" : "#5a667a",
  fontWeight: active ? 500 : 400,
  transition: "all .15s"
});

/**
 * 顶栏意见反馈入口：按钮 + 弹窗，提交至 AI4MS 统一门户后端。
 *
 * Returns:
 *     圆形图标按钮，点击后弹出反馈提交弹窗。
 */
export default function FeedbackButton() {
  const { user } = useAuth();
  const [open, setOpen] = useState(false);
  const [feedbackType, setFeedbackType] = useState("bug");
  const [content, setContent] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const username = user?.username || "当前登录用户";
  const canSubmit = useMemo(
    () => content.trim().length > 0 && !submitting,
    [content, submitting]
  );

  /** 打开弹窗并重置表单。 */
  const openDialog = () => {
    setFeedbackType("bug");
    setContent("");
    setOpen(true);
  };

  /** 提交反馈。 */
  const handleSubmit = async () => {
    const text = content.trim();
    if (!text) {
      message.warning("请填写反馈内容");
      return;
    }
    setSubmitting(true);
    try {
      const headers = { "Content-Type": "application/json" };
      const token = sessionStorage.getItem(AUTH_TOKEN_KEY);
      if (token) {
        headers.Authorization = `Bearer ${token}`;
      }
      const resp = await fetch(AI4MS_FEEDBACK_URL, {
        method: "POST",
        headers,
        body: JSON.stringify({
          platform: FEEDBACK_PLATFORM,
          feedback_type: feedbackType,
          content: text
        })
      });
      if (resp.status === 401) {
        message.error("登录状态已失效，请重新从 AI4MS 门户进入后再提交");
        return;
      }
      if (!resp.ok) {
        message.error("提交失败，请稍后重试");
        return;
      }
      setOpen(false);
      message.success("提交成功，感谢您的反馈");
    } catch {
      message.error("网络异常，提交失败");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <>
      <Tooltip title="意见反馈" placement="bottom">
        <Button
          shape="circle"
          aria-label="意见反馈"
          icon={<FeedbackIcon />}
          onClick={openDialog}
        />
      </Tooltip>

      <Modal
        title="意见反馈"
        open={open}
        onCancel={() => setOpen(false)}
        width={480}
        destroyOnClose
        footer={
          <Space>
            <Button onClick={() => setOpen(false)}>取消</Button>
            <Button
              type="primary"
              loading={submitting}
              disabled={!canSubmit}
              onClick={handleSubmit}
            >
              提交反馈
            </Button>
          </Space>
        }
      >
        <div style={{ fontSize: 12, color: "rgba(0,0,0,0.45)", margin: "-4px 0 16px" }}>
          您的反馈将提交至 AI4MS 平台管理员，感谢帮助我们一起改进
        </div>

        <div style={{ fontSize: 13, color: "rgba(0,0,0,0.65)", marginBottom: 8 }}>
          <span style={{ color: "#ff4d4f", marginRight: 3 }}>*</span>反馈类型
        </div>
        <div style={{ display: "flex", gap: 8, marginBottom: 16, flexWrap: "wrap" }}>
          {FEEDBACK_TYPES.map((t) => (
            <button
              key={t.value}
              type="button"
              style={chipStyle(feedbackType === t.value)}
              onClick={() => setFeedbackType(t.value)}
            >
              {t.label}
            </button>
          ))}
        </div>

        <div style={{ fontSize: 13, color: "rgba(0,0,0,0.65)", marginBottom: 8 }}>
          <span style={{ color: "#ff4d4f", marginRight: 3 }}>*</span>反馈内容
        </div>
        <Input.TextArea
          rows={5}
          maxLength={MAX_CONTENT_LENGTH}
          showCount
          value={content}
          onChange={(e) => setContent(e.target.value)}
          placeholder="请详细描述您遇到的问题或建议，如操作路径、预期效果、实际现象…"
        />

        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 8,
            marginTop: 14,
            fontSize: 12,
            color: "rgba(0,0,0,0.45)"
          }}
        >
          提交人：<b style={{ color: "rgba(0,0,0,0.65)", fontWeight: 500 }}>{username}</b>
        </div>
      </Modal>
    </>
  );
}
