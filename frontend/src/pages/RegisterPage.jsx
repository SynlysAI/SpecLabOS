import React from "react";
import { Button, Card, Form, Input, Typography, message } from "antd";
import { Link, useNavigate } from "react-router-dom";

import { useAuth } from "../auth/AuthContext";

const { Text, Title } = Typography;

/**
 * 注册页面。
 *
 * Returns:
 *     AI4MS 邀请码注册表单。
 */
export default function RegisterPage() {
  const navigate = useNavigate();
  const { loading, signUp } = useAuth();

  /**
   * 提交注册表单。
   *
   * Args:
   *     values: 表单字段值。
   */
  const handleSubmit = async (values) => {
    try {
      await signUp({
        invite_code: values.invite_code.trim(),
        username: values.username.trim(),
        password: values.password,
        organization: values.organization?.trim() || ""
      });
      message.success("注册成功");
      navigate("/", { replace: true });
    } catch (error) {
      message.error(error.response?.data?.detail || "注册失败，请检查邀请码和账号信息");
    }
  };

  return (
    <main className="auth-page">
      <section className="auth-hero">
        <div className="auth-brand-mark">
          <img src="/JG-logo.png" alt="JG Logo" />
        </div>
        <Title level={1} className="auth-title">
          创建统一账号
        </Title>
        <Text className="auth-subtitle">
          注册后账号密码将与 AI4MS 门户互通
        </Text>
      </section>
      <Card className="auth-card auth-register-card">
        <Title level={3} className="auth-card-title">
          邀请码注册
        </Title>
        <Form layout="vertical" onFinish={handleSubmit} requiredMark={false}>
          <Form.Item
            label="邀请码"
            name="invite_code"
            rules={[{ required: true, message: "请输入邀请码" }]}
          >
            <Input size="large" placeholder="请输入 AI4MS 邀请码" />
          </Form.Item>
          <Form.Item
            label="用户名"
            name="username"
            rules={[{ required: true, message: "请输入用户名" }]}
          >
            <Input size="large" placeholder="用于登录 AI4MS 和 SpecLabOS" />
          </Form.Item>
          <Form.Item label="单位" name="organization">
            <Input size="large" placeholder="可选，例如：嘉庚创新实验室" />
          </Form.Item>
          <Form.Item
            label="密码"
            name="password"
            rules={[
              { required: true, message: "请输入密码" },
              { min: 6, message: "密码至少 6 位" }
            ]}
          >
            <Input.Password size="large" placeholder="请输入密码" autoComplete="new-password" />
          </Form.Item>
          <Form.Item
            label="确认密码"
            name="confirm_password"
            dependencies={["password"]}
            rules={[
              { required: true, message: "请再次输入密码" },
              ({ getFieldValue }) => ({
                validator(_, value) {
                  if (!value || getFieldValue("password") === value) {
                    return Promise.resolve();
                  }
                  return Promise.reject(new Error("两次输入的密码不一致"));
                }
              })
            ]}
          >
            <Input.Password size="large" placeholder="请再次输入密码" autoComplete="new-password" />
          </Form.Item>
          <Button
            type="primary"
            htmlType="submit"
            size="large"
            block
            loading={loading}
            className="auth-submit"
          >
            注册并登录
          </Button>
        </Form>
        <Text type="secondary" className="auth-switch">
          已有账号？<Link to="/login">返回登录</Link>
        </Text>
      </Card>
    </main>
  );
}
