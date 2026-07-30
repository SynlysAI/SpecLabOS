import React, { useRef, useState } from "react";
import { Button, Card, Input, Space, Tabs, Typography, message } from "antd";
import {
  ClearOutlined,
  CopyOutlined,
  ExperimentOutlined,
  SearchOutlined,
  SendOutlined,
  TableOutlined
} from "@ant-design/icons";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeHighlight from "rehype-highlight";
import "highlight.js/styles/github.css";
import { streamScienceChat } from "../services/scienceChatApi";

const { Text, Paragraph } = Typography;
const { TextArea } = Input;

const PRODUCT_TABS = [
  {
    key: "sciverse",
    label: (
      <Space>
        <SearchOutlined />
        <span>Sciverse 文献检索</span>
      </Space>
    )
  },
  {
    key: "dianshi",
    label: (
      <Space>
        <ExperimentOutlined />
        <span>点石 DianShi 化学检索</span>
      </Space>
    )
  },
  {
    key: "seqstudio",
    label: (
      <Space>
        <TableOutlined />
        <span>SeqStudio 蛋白质分析</span>
      </Space>
    )
  }
];

/**
 * 渲染 Markdown 内容（助手回复气泡专用）。
 * 支持 GFM 表格、代码块（rehype-highlight 高亮）、列表、链接等。
 *
 * Args:
 *     content: 待渲染的 Markdown 字符串。
 */
function MessageContent({ content }) {
  return (
    <div className="chat-markdown">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[rehypeHighlight]}
        components={{
          a: ({ node, ...props }) => <a target="_blank" rel="noreferrer" {...props} />
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
}

/**
 * 科学数据助手页面 — 统一的自然语言科学数据查询入口。
 *
 * Returns:
 *     含产品 Tab 切换与流式对话的交互界面。
 */
export default function ScienceDataAssistant() {
  const [activeTab, setActiveTab] = useState("sciverse");
  const [inputText, setInputText] = useState("");
  const [messages, setMessages] = useState([]);
  const [streamingText, setStreamingText] = useState("");
  const [loading, setLoading] = useState(false);
  const controllerRef = useRef(null);
  const chatEndRef = useRef(null);

  /**
   * 发送消息，触发 SSE 流式对话。
   */
  function handleSend() {
    const text = inputText.trim();
    if (!text || loading) return;

    const userMsg = { role: "user", content: text };
    setMessages((prev) => [...prev, userMsg]);
    setInputText("");
    setStreamingText("");
    setLoading(true);

    controllerRef.current = streamScienceChat(
      activeTab,
      text,
      (chunk) => {
        setStreamingText((prev) => prev + chunk);
      },
      (fullText) => {
        setMessages((prev) => [
          ...prev,
          { role: "assistant", content: fullText, error: false }
        ]);
        setStreamingText("");
        setLoading(false);
      }
    );
  }

  /**
   * 停止当前请求。
   */
  function handleStop() {
    if (controllerRef.current) {
      controllerRef.current.abort();
      controllerRef.current = null;
    }
    if (streamingText) {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: streamingText + "\n\n[已中断]", error: false }
      ]);
    }
    setStreamingText("");
    setLoading(false);
  }

  /**
   * 清空对话历史。
   */
  function handleClear() {
    handleStop();
    setMessages([]);
    setStreamingText("");
  }

  /**
   * 复制最后一条助手回复。
   */
  async function handleCopy() {
    const lastAssistant = [...messages].reverse().find((m) => m.role === "assistant");
    const text = lastAssistant?.content || streamingText;
    if (!text) return;
    try {
      await navigator.clipboard.writeText(text);
      message.success("已复制到剪贴板");
    } catch {
      message.error("复制失败");
    }
  }

  const { placeholder, introText } = getProductConfig(activeTab);

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
      <ModelProviderBanner />

      {/* 产品 Tab */}
      <Tabs
        activeKey={activeTab}
        onChange={(key) => {
          setActiveTab(key);
          handleClear();
        }}
        items={PRODUCT_TABS.map((tab) => ({
          key: tab.key,
          label: tab.label,
          disabled: tab.key === "seqstudio"
        }))}
      />

      {/* SeqStudio 占位 */}
      {activeTab === "seqstudio" && <SeqStudioPlaceholder />}

      {/* 对话区域 */}
      {activeTab !== "seqstudio" && (
        <>
          <Card
            size="small"
            style={{ flex: 1 }}
            bodyStyle={{
              display: "flex",
              flexDirection: "column",
              height: "calc(100vh - 380px)",
              minHeight: 360
            }}
          >
            {/* 消息列表 */}
            <div
              style={{
                flex: 1,
                overflow: "auto",
                marginBottom: 12
              }}
            >
              {messages.length === 0 && !loading && (
                <div style={{ textAlign: "center", padding: "60px 20px" }}>
                  <SearchOutlined
                    style={{ fontSize: 36, color: "#1677ff", marginBottom: 16 }}
                  />
                  <Paragraph type="secondary">{introText}</Paragraph>
                </div>
              )}

              {messages.map((msg, idx) => (
                <div
                  key={idx}
                  style={{
                    marginBottom: 12,
                    display: "flex",
                    justifyContent: msg.role === "user" ? "flex-end" : "flex-start"
                  }}
                >
                  <div
                    style={{
                      maxWidth: "80%",
                      padding: "8px 14px",
                      borderRadius: 12,
                      background: msg.role === "user" ? "#1677ff" : "#f0f2f5",
                      color: msg.role === "user" ? "#fff" : "#333",
                      fontSize: 14,
                      lineHeight: 1.7
                    }}
                  >
                    {msg.role === "user" ? (
                      <span style={{ whiteSpace: "pre-wrap" }}>{msg.content}</span>
                    ) : (
                      <MessageContent content={msg.content} />
                    )}
                  </div>
                </div>
              ))}

              {/* 流式生成中 */}
              {streamingText && (
                <div style={{ marginBottom: 12, display: "flex", justifyContent: "flex-start" }}>
                  <div
                    style={{
                      maxWidth: "80%",
                      padding: "8px 14px",
                      borderRadius: 12,
                      background: "#f0f2f5",
                      color: "#333",
                      fontSize: 14,
                      lineHeight: 1.7
                    }}
                  >
                    <MessageContent content={streamingText} />
                  </div>
                </div>
              )}
              <div ref={chatEndRef} />
            </div>
          </Card>

          {/* 输入区域 */}
          <Card size="small">
            <TextArea
              rows={3}
              placeholder={placeholder}
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              disabled={loading}
              onPressEnter={(e) => {
                if (!e.shiftKey) {
                  e.preventDefault();
                  handleSend();
                }
              }}
            />
            <Space style={{ marginTop: 12 }}>
              <Button
                type="primary"
                icon={<SendOutlined />}
                onClick={handleSend}
                loading={loading}
                disabled={!inputText.trim()}
              >
                {loading ? "生成中..." : "发送"}
              </Button>
              {loading && (
                <Button danger onClick={handleStop}>
                  停止
                </Button>
              )}
              <Button icon={<ClearOutlined />} onClick={handleClear}>
                清空对话
              </Button>
              <Button
                icon={<CopyOutlined />}
                onClick={handleCopy}
                disabled={!streamingText && messages.length === 0}
              >
                复制回复
              </Button>
            </Space>
          </Card>
        </>
      )}
    </div>
  );
}

/**
 * 模型服务来源品牌说明横幅。
 */
function ModelProviderBanner() {
  return (
    <Card
      size="small"
      bodyStyle={{ padding: "10px 16px" }}
      style={{
        border: "1px solid rgba(22, 119, 255, 0.14)",
        background: "linear-gradient(135deg, #f8fbff 0%, #ffffff 100%)",
        boxShadow: "0 6px 18px rgba(15, 23, 42, 0.04)"
      }}
    >
      <Space size={14} align="center" wrap>
        <img
          src="/上海人工智能实验室.png"
          alt="上海人工智能实验室 Logo"
          style={{
            display: "block",
            width: 118,
            maxWidth: "32vw",
            height: "auto"
          }}
        />
        <div>
          <Text strong style={{ display: "block", fontSize: 15, color: "#123b70" }}>
            模型服务来自上海人工智能实验室
          </Text>
          <Text type="secondary" style={{ fontSize: 13 }}>
            为科学文献检索、化学数据查询与蛋白质分析提供智能模型能力支持。
          </Text>
        </div>
      </Space>
    </Card>
  );
}

/**
 * 根据当前产品 Tab 返回输入提示和介绍文本。
 *
 * Args:
 *     product: 当前选中的产品 key。
 *
 * Returns:
 *     包含 placeholder 和 introText 的对象。
 */
function getProductConfig(product) {
  switch (product) {
    case "sciverse":
      return {
        placeholder: "输入你的研究问题，例如：\n找石墨烯电池循环稳定性近3年的高被引论文\n检索 COVID-19 疫苗有效性的 meta 分析",
        introText:
          "面向 Agent 的科学文献检索与元数据查询平台。\n"
          + "支持智能文献片段检索（agentic-search）、结构化筛选（meta-search）、全文读取（content）和附件下载（resource）。\n"
          + "用自然语言描述你的研究问题，AI 将自动选择合适的检索方式并整理结果。"
      };
    case "dianshi":
      return {
        placeholder: "输入化学查询，例如：\n搜索阿司匹林的结构相似物质\n查找 Suzuki 偶联反应的最优条件\n搜索含苯环结构的化合物",
        introText:
          "大规模化学信息检索与逆合成 RAG 平台。\n"
          + "覆盖千万级化学物质、亿级反应、百万级专利文献。\n"
          + "支持物质检索、相似度搜索、子结构搜索、反应检索与逆合成分析。"
      };
    default:
      return { placeholder: "", introText: "" };
  }
}

/**
 * SeqStudio 产品占位 — 无公开 API，引导在线访问。
 */
function SeqStudioPlaceholder() {
  return (
    <Card style={{ textAlign: "center", padding: "60px 20px" }}>
      <TableOutlined style={{ fontSize: 48, color: "#1677ff", marginBottom: 24 }} />
      <Paragraph style={{ fontSize: 16, maxWidth: 560, margin: "0 auto 24px" }}>
        SeqStudio 是蛋白质功能注释的 AI 推理平台，整合 BLAST · InterProScan · Foldseek · TMHMM
        等多源证据，结合 LLM 生成结构化注释。当前仅提供在线访问与本地部署方式，暂无公开 HTTP
        API，待开放后补充接入。
      </Paragraph>
      <Button
        type="primary"
        size="large"
        href="https://sciverse.space/docs#seqstudio/overview"
        target="_blank"
      >
        前往 SeqStudio 在线工作台
      </Button>
    </Card>
  );
}
