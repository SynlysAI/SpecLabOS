import React, { useEffect, useMemo, useState } from "react";
import {
  Alert,
  Button,
  Card,
  DatePicker,
  Empty,
  Form,
  Input,
  List,
  Select,
  Space,
  Tag,
  Typography
} from "antd";
import dayjs from "dayjs";

import PageToolbar from "../components/PageToolbar";
import { fetchLogContent, fetchSystemLogs } from "../services/logApi";
import { formatDateTime } from "../utils/datetime";

const { Paragraph, Text } = Typography;

const DEFAULT_FILTERS = {
  keyword: "",
  device_id: "",
  date: null,
  days: 7
};

/** 可按文本日志预览的文件扩展名。 */
const TEXT_LOG_EXTENSIONS = [".log", ".txt", ".csv", ".json", ".xml"];

/**
 * 判断日志文件是否为可预览的文本类文件。
 *
 * Args:
 *     file: 日志文件记录。
 *
 * Returns:
 *     文本类文件返回 true。
 */
function isTextLogFile(file) {
  const contentType = String(file?.content_type || "").toLowerCase();
  const filename = String(file?.filename || "").toLowerCase();
  if (contentType.startsWith("text/") || contentType.includes("json") || contentType.includes("xml")) {
    return true;
  }
  return TEXT_LOG_EXTENSIONS.some((extension) => filename.endsWith(extension));
}

/**
 * 从常见日志行首提取时间。
 *
 * Args:
 *     line: 单行日志文本。
 *
 * Returns:
 *     识别到的时间文本；无法识别时返回空字符串。
 */
function extractLineTime(line) {
  const match = String(line || "").match(
    /(\d{4}[-/]\d{2}[-/]\d{2}[ T]\d{2}:\d{2}:\d{2}(?:[.,]\d{1,6})?)/
  );
  return match ? match[1].replace("T", " ") : "";
}

/**
 * 格式化文件大小。
 *
 * Args:
 *     value: 字节数。
 *
 * Returns:
 *     带单位的文件大小文本。
 */
function formatBytes(value) {
  const size = Number(value || 0);
  if (size < 1024) return `${size} B`;
  if (size < 1024 ** 2) return `${(size / 1024).toFixed(1)} KB`;
  return `${(size / 1024 ** 2).toFixed(1)} MB`;
}

/**
 * 格式化时间文本。
 *
 * Args:
 *     value: 后端返回的时间文本。
 *
 * Returns:
 *     去掉时区和微秒后的短时间文本。
 */
/**
 * 提取接口请求失败原因。
 *
 * Args:
 *     error: 请求异常对象。
 *
 * Returns:
 *     可直接展示给用户的失败原因文本。
 */
function buildRequestErrorMessage(error) {
  const detail = error?.response?.data?.detail;
  if (typeof detail === "string" && detail.trim()) {
    return detail;
  }
  if (error?.message === "Network Error") {
    return "无法连接后端服务，请确认服务已启动。";
  }
  return error?.message || "请求失败，请检查后端服务状态。";
}

/**
 * 按关键字拆分文本，保留匹配片段用于高亮。
 *
 * Args:
 *     text: 原始文本。
 *     keyword: 搜索关键字。
 *
 * Returns:
 *     文本片段列表。
 */
function splitByKeyword(text, keyword) {
  const normalizedKeyword = keyword.trim();
  if (!normalizedKeyword) return [text];
  const pattern = new RegExp(`(${normalizedKeyword.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")})`, "ig");
  return text.split(pattern);
}

/**
 * 设备日志页。
 *
 * Returns:
 *     展示数据中心日志文件和原文内容。
 */
export default function SystemLogsPage() {
  const [form] = Form.useForm();
  const [files, setFiles] = useState([]);
  const [selectedFile, setSelectedFile] = useState(null);
  const [content, setContent] = useState("");
  const [truncated, setTruncated] = useState(false);
  const [contentKeyword, setContentKeyword] = useState("");
  const [loading, setLoading] = useState(false);
  const [contentLoading, setContentLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");
  const [deviceIds, setDeviceIds] = useState([]);

  const deviceOptions = useMemo(() => ([
    { label: "全部设备", value: "" },
    ...deviceIds.map((deviceId) => ({ label: deviceId, value: deviceId }))
  ]), [deviceIds]);

  /**
   * 加载日志文件列表。
   *
   * Args:
   *     filters: 查询筛选条件。
   */
  async function loadFiles(filters = form.getFieldsValue()) {
    setLoading(true);
    try {
      const response = await fetchSystemLogs({
        ...DEFAULT_FILTERS,
        ...filters,
        date: filters.date?.format ? filters.date.format("YYYY-MM-DD") : undefined,
        days: filters.date ? undefined : 7
      });
      setFiles(response.items);
      if (!filters.device_id) {
        setDeviceIds([...new Set(response.items.map((item) => item.device_id).filter(Boolean))]);
      }
      setErrorMessage("");
      const nextFile = response.items.find((item) => item.file_id === selectedFile?.file_id) || response.items[0];
      if (nextFile) {
        openFile(nextFile);
      } else {
        setSelectedFile(null);
        setContent("");
      }
    } catch (error) {
      setFiles([]);
      setSelectedFile(null);
      setContent("");
      setErrorMessage(buildRequestErrorMessage(error));
    } finally {
      setLoading(false);
    }
  }

  /**
   * 打开日志文件内容。
   *
   * Args:
   *     file: 日志文件记录。
   */
  async function openFile(file) {
    setSelectedFile(file);
    if (!isTextLogFile(file)) {
      setContent("");
      setTruncated(false);
      setErrorMessage("");
      return;
    }
    setContentLoading(true);
    try {
      const response = await fetchLogContent(file.file_id);
      setContent(response.content || "");
      setTruncated(Boolean(response.truncated));
      setErrorMessage("");
    } catch (error) {
      setContent("");
      setErrorMessage(buildRequestErrorMessage(error));
    } finally {
      setContentLoading(false);
    }
  }

  useEffect(() => {
    form.setFieldsValue(DEFAULT_FILTERS);
    loadFiles(DEFAULT_FILTERS);
  }, []);

  const lines = content.split(/\r?\n/);
  const visibleLines = contentKeyword.trim()
    ? lines.filter((line) => line.toLowerCase().includes(contentKeyword.trim().toLowerCase()))
    : lines;

  return (
    <section className="page-section">
      <PageToolbar />
      {errorMessage ? (
        <Alert type="error" showIcon message="日志加载失败" description={errorMessage} style={{ marginBottom: 16 }} />
      ) : null}
      <Card title="设备日志" className="device-log-card">
        <Form form={form} layout="inline" onFinish={loadFiles} style={{ marginBottom: 16 }}>
          <Form.Item name="device_id" style={{ marginBottom: 8 }}>
            <Select options={deviceOptions} style={{ width: 180 }} placeholder="全部设备" />
          </Form.Item>
          <Form.Item name="date" style={{ marginBottom: 8 }}>
            <DatePicker placeholder="指定日期" style={{ width: 150 }} />
          </Form.Item>
          <Form.Item name="keyword" style={{ marginBottom: 8 }}>
            <Input allowClear placeholder="文件名 / 路径" style={{ width: 220 }} />
          </Form.Item>
          <Form.Item style={{ marginBottom: 8 }}>
            <Space>
              <Button htmlType="submit" type="primary">查询</Button>
              <Button
                onClick={() => {
                  form.setFieldsValue(DEFAULT_FILTERS);
                  loadFiles(DEFAULT_FILTERS);
                }}
              >
                最近 7 天
              </Button>
            </Space>
          </Form.Item>
        </Form>
        <div className="device-log-layout">
          <Card size="small" title={`日志文件 ${files.length}`} className="device-log-list" loading={loading}>
            {files.length ? (
              <List
                dataSource={files}
                renderItem={(item) => (
                  <List.Item
                    className={item.file_id === selectedFile?.file_id ? "device-log-item is-active" : "device-log-item"}
                    onClick={() => openFile(item)}
                  >
                    <div>
                      <Text strong>{item.filename || "未命名日志"}</Text>
                      <div className="device-log-meta">
                        <Tag>{item.device_id || "未知设备"}</Tag>
                        <span>{formatBytes(item.file_size)}</span>
                      </div>
                      <Text type="secondary">{formatDateTime(item.ingested_at)}</Text>
                    </div>
                  </List.Item>
                )}
              />
            ) : (
              <Empty description="最近没有日志文件" />
            )}
          </Card>
          <Card
            size="small"
            className="device-log-viewer"
            loading={contentLoading}
            title={selectedFile ? selectedFile.filename : "日志内容"}
            extra={selectedFile && isTextLogFile(selectedFile) ? (
              <Input
                allowClear
                value={contentKeyword}
                placeholder="在内容中搜索"
                style={{ width: 180 }}
                onChange={(event) => setContentKeyword(event.target.value)}
              />
            ) : undefined}
          >
            {selectedFile ? (
              isTextLogFile(selectedFile) ? (
                <>
                  <Paragraph type="secondary" className="device-log-path">
                    {selectedFile.device_id} / {selectedFile.relative_path || selectedFile.filename}
                    {truncated ? " · 仅显示文件尾部" : ""}
                  </Paragraph>
                  <div className="device-log-content">
                    {visibleLines.map((line, index) => {
                      const lineTime = extractLineTime(line);
                      return (
                        <div className="device-log-line" key={`${index}-${line.slice(0, 24)}`}>
                          <span className="device-log-time">{lineTime || "--"}</span>
                          <span>
                            {splitByKeyword(line, contentKeyword).map((part, partIndex) => (
                              part.toLowerCase() === contentKeyword.trim().toLowerCase() && contentKeyword.trim()
                                ? <mark key={partIndex}>{part}</mark>
                                : <span key={partIndex}>{part || " "}</span>
                            ))}
                          </span>
                        </div>
                      );
                    })}
                  </div>
                </>
              ) : (
                <Empty description="不支持该格式日志预览" />
              )
            ) : (
              <Empty description="选择左侧日志文件查看内容" />
            )}
          </Card>
        </div>
      </Card>
    </section>
  );
}
