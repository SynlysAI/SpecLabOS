import React from "react";
import { Alert, Button, Card, Form, Input, Typography, message } from "antd";
import { Link, useLocation, useNavigate } from "react-router-dom";

import { useAuth } from "../auth/AuthContext";

const { Text, Title } = Typography;

/**
 * 登录页面。
 *
 * Returns:
 *     统一账号密码登录表单。
 */
export default function LoginPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const { loading, signIn } = useAuth();
  const from = location.state?.from?.pathname || "/";

  /**
   * 提交登录表单。
   *
   * Args:
   *     values: 表单字段值。
   */
  const handleSubmit = async (values) => {
    try {
      await signIn(values.username.trim(), values.password);
      message.success("登录成功");
      navigate(from, { replace: true });
    } catch (error) {
      message.error(error.response?.data?.detail || "登录失败，请检查账号密码");
    }
  };

  return (
    <main className="auth-page">
      <section className="auth-hero">
        <div className="auth-brand-mark">
          <img src="/JG-logo.png" alt="JG Logo" />
        </div>
        <Title level={1} className="auth-title">
          SpecLabOS
        </Title>
        <Text className="auth-subtitle">
          使用 AI4MS 统一门户账号登录实验管理平台
        </Text>
      </section>
      <Card className="auth-card">
        <Title level={3} className="auth-card-title">
          账号登录
        </Title>
        <Alert
          showIcon
          type="info"
          className="auth-tip"
          message="已从 AI4MS 门户进入时会自动免登录；也可以在这里手动登录。"
        />
        <Form layout="vertical" onFinish={handleSubmit} requiredMark={false}>
          <Form.Item
            label="用户名"
            name="username"
            rules={[{ required: true, message: "请输入用户名" }]}
          >
            <Input size="large" placeholder="请输入 AI4MS 用户名" autoComplete="username" />
          </Form.Item>
          <Form.Item
            label="密码"
            name="password"
            rules={[{ required: true, message: "请输入密码" }]}
          >
            <Input.Password
              size="large"
              placeholder="请输入密码"
              autoComplete="current-password"
            />
          </Form.Item>
          <Button
            type="primary"
            htmlType="submit"
            size="large"
            block
            loading={loading}
            className="auth-submit"
          >
            登录
          </Button>
        </Form>
        <Text type="secondary" className="auth-switch">
          还没有账号？<Link to="/register">使用邀请码注册</Link>
        </Text>
      </Card>
    </main>
  );
}
