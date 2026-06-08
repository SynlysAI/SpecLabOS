import React, { useRef, useState } from "react";
import { Button, Card, Input, Space, Spin, Typography, message } from "antd";
import {
  ClearOutlined,
  CopyOutlined,
  SendOutlined
} from "@ant-design/icons";
import { streamParseInstructions } from "../services/toolsApi";

const { Text } = Typography;
const { TextArea } = Input;

/**
 * 树脂合成指令解析子页签。
 *
 * Returns:
 *     提供实验方案输入、流式生成指令、最终指令列表展示的交互界面。
 */
export default function InstructionParserTab() {
  const [experimentPlan, setExperimentPlan] = useState("");
  const [outputText, setOutputText] = useState("");
  const [instructions, setInstructions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [streamDone, setStreamDone] = useState(false);
  const controllerRef = useRef(null);

  /**
   * 开始解析实验方案。
   */
  function handleParse() {
    if (!experimentPlan.trim()) return;

    setOutputText("");
    setInstructions([]);
    setStreamDone(false);
    setLoading(true);

    controllerRef.current = streamParseInstructions(
      experimentPlan,
      (chunk) => {
        setOutputText((prev) => prev + chunk);
      },
      (instructionList, _fullText) => {
        setInstructions(instructionList);
        setStreamDone(true);
        setLoading(false);
      }
    );
  }

  /**
   * 停止当前请求并重置状态。
   */
  function handleStop() {
    if (controllerRef.current) {
      controllerRef.current.abort();
      controllerRef.current = null;
    }
    setLoading(false);
  }

  /**
   * 清空所有内容。
   */
  function handleClear() {
    handleStop();
    setExperimentPlan("");
    setOutputText("");
    setInstructions([]);
    setStreamDone(false);
  }

  /**
   * 复制指令列表到剪贴板。
   */
  async function handleCopyInstructions() {
    try {
      await navigator.clipboard.writeText(instructions.join("\n"));
      message.success("已复制到剪贴板");
    } catch {
      message.error("复制失败");
    }
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
      {/* 输入区域 */}
      <Card size="small" title="实验方案输入">
        <TextArea
          rows={5}
          placeholder={"请输入实验方案文本，例如：\n1. 向反应釜中加入100ml 苯乙烯\n2. 加热至80°C\n3. 搅拌30分钟..."}
          value={experimentPlan}
          onChange={(e) => setExperimentPlan(e.target.value)}
          disabled={loading}
        />
        <Space style={{ marginTop: 12 }}>
          <Button
            type="primary"
            icon={<SendOutlined />}
            onClick={handleParse}
            loading={loading}
            disabled={!experimentPlan.trim()}
          >
            解析指令
          </Button>
          {loading && (
            <Button danger onClick={handleStop}>
              停止
            </Button>
          )}
          <Button icon={<ClearOutlined />} onClick={handleClear}>
            清空
          </Button>
        </Space>
      </Card>

      {/* 流式输出区域 */}
      <Card
        size="small"
        title={
          <Space>
            <span>生成过程</span>
            {loading && <Spin size="small" />}
          </Space>
        }
      >
        <div
          style={{
            maxHeight: 260,
            overflow: "auto",
            whiteSpace: "pre-wrap",
            fontFamily: "monospace",
            fontSize: 13,
            background: "#f6f8fa",
            borderRadius: 8,
            padding: 12,
            minHeight: 80
          }}
        >
          {outputText || (
            <Text type="secondary">点击"解析指令"开始生成...</Text>
          )}
        </div>
      </Card>

      {/* 最终指令列表 */}
      {streamDone && instructions.length > 0 && (
        <Card
          size="small"
          title={
            <Space>
              <span>解析结果（{instructions.length} 条指令）</span>
            </Space>
          }
          extra={
            <Button
              size="small"
              icon={<CopyOutlined />}
              onClick={handleCopyInstructions}
            >
              复制指令
            </Button>
          }
        >
          <div
            style={{
              fontFamily: "monospace",
              fontSize: 13,
              lineHeight: 2
            }}
          >
            {instructions.map(function(inst, idx) {
              return (
                <div
                  key={idx}
                  style={{
                    padding: "4px 8px",
                    background: idx % 2 === 0 ? "#f6f8fa" : "transparent",
                    borderRadius: 4
                  }}
                >
                  <Text code>{inst}</Text>
                </div>
              );
            })}
          </div>
        </Card>
      )}

      {/* 无指令时的提示 */}
      {streamDone && instructions.length === 0 && (
        <Card size="small">
          <Text type="secondary">未解析出以 "S " 开头的指令，请检查实验方案或重试。</Text>
        </Card>
      )}
    </div>
  );
}
