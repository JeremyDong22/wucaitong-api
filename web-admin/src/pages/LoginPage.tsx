// v1.1 - 登录页（手机号+短信验证码 + 开发模式快捷登录）
import { useState } from 'react'
import { Card, Form, Input, Button, Typography, message, Divider } from 'antd'
import { MobileOutlined, LockOutlined, ThunderboltOutlined } from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import { authService } from '../services/auth'
import { useAuthStore } from '../stores/auth'

const { Title, Text } = Typography

// 测试账号（仅开发环境显示）
const DEV_ACCOUNTS = [
  { phone: '13800000001', label: '平台管理员', role: 'W' },
  { phone: '13800000002', label: '收购商 C', role: 'C' },
  { phone: '13800000003', label: '贸易商 B', role: 'B' },
  { phone: '13800000004', label: '供应商 A', role: 'A' },
  { phone: '13800000005', label: '经纪人', role: 'BROKER' },
  { phone: '13800000006', label: '司机', role: 'DRIVER' },
  { phone: '13800000007', label: '仓管员', role: 'WAREHOUSE_KEEPER' },
]

export default function LoginPage() {
  const [form] = Form.useForm()
  const [smsSent, setSmsSent] = useState(false)
  const [countdown, setCountdown] = useState(0)
  const [loading, setLoading] = useState(false)
  const [quickLoading, setQuickLoading] = useState<string | null>(null)
  const { setAuth } = useAuthStore()
  const navigate = useNavigate()

  const doNavigate = (role: string) => {
    if (role === 'W') {
      navigate('/platform/dashboard')
    } else {
      navigate('/merchant/dashboard')
    }
  }

  const handleSendSms = async () => {
    const phone = form.getFieldValue('phone')
    if (!phone || phone.length !== 11) {
      message.warning('请输入正确的手机号')
      return
    }
    try {
      await authService.sendSms(phone)
      setSmsSent(true)
      setCountdown(60)
      const timer = setInterval(() => {
        setCountdown((c) => {
          if (c <= 1) { clearInterval(timer); return 0 }
          return c - 1
        })
      }, 1000)
      message.success('验证码已发送')
    } catch {}
  }

  const handleLogin = async (values: { phone: string; code: string }) => {
    setLoading(true)
    try {
      const res = await authService.loginByPhone(values.phone, values.code)
      setAuth(res.access_token, res.role, res.user_id)
      message.success('登录成功')
      doNavigate(res.role)
    } finally {
      setLoading(false)
    }
  }

  // 快捷登录：自动获取 debug_code 再登录，一键完成
  const handleQuickLogin = async (phone: string) => {
    setQuickLoading(phone)
    try {
      const smsRes = await authService.sendSms(phone) as { debug_code?: string }
      const code = smsRes?.debug_code
      if (!code) {
        message.error('未获取到验证码，请确认是开发环境')
        return
      }
      const res = await authService.loginByPhone(phone, code)
      setAuth(res.access_token, res.role, res.user_id)
      message.success('登录成功')
      doNavigate(res.role)
    } finally {
      setQuickLoading(null)
    }
  }

  return (
    <div style={{
      minHeight: '100vh', display: 'flex', alignItems: 'center',
      justifyContent: 'center', background: '#f0f2f5',
    }}>
      <Card style={{ width: 420, borderRadius: 12, boxShadow: '0 4px 20px rgba(0,0,0,0.1)' }}>
        <div style={{ textAlign: 'center', marginBottom: 32 }}>
          <Title level={2} style={{ margin: 0, color: '#1677ff' }}>物采通</Title>
          <Text type="secondary">废旧物资收购交易平台</Text>
        </div>

        <Form form={form} onFinish={handleLogin} layout="vertical" size="large">
          <Form.Item name="phone" rules={[{ required: true, message: '请输入手机号' }]}>
            <Input prefix={<MobileOutlined />} placeholder="手机号" maxLength={11} />
          </Form.Item>
          <Form.Item name="code" rules={[{ required: true, message: '请输入验证码' }]}>
            <Input
              prefix={<LockOutlined />}
              placeholder="短信验证码"
              maxLength={6}
              addonAfter={
                <Button
                  type="link" size="small"
                  disabled={countdown > 0}
                  onClick={handleSendSms}
                  style={{ padding: 0 }}
                >
                  {countdown > 0 ? `${countdown}s` : (smsSent ? '重新获取' : '获取验证码')}
                </Button>
              }
            />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" block loading={loading}>
              登录
            </Button>
          </Form.Item>
        </Form>

        {/* 开发环境快捷登录 */}
        <Divider style={{ margin: '8px 0 16px' }}>
          <Text type="secondary" style={{ fontSize: 12 }}>
            <ThunderboltOutlined /> 测试快捷登录
          </Text>
        </Divider>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
          {DEV_ACCOUNTS.map((acc) => (
            <Button
              key={acc.phone}
              size="small"
              loading={quickLoading === acc.phone}
              onClick={() => handleQuickLogin(acc.phone)}
              style={{ fontSize: 12, height: 32 }}
            >
              {acc.label}
            </Button>
          ))}
        </div>
      </Card>
    </div>
  )
}
