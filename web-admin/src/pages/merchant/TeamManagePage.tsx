// v1.0 - 团队管理页（准入供应商 / 邀请司机 / 添加仓管员）
import { useState } from 'react'
import {
  Card, Tabs, Form, Input, Button, message,
} from 'antd'
import { merchantService } from '../../services/merchant'

function SupplierAdmitForm() {
  const [form] = Form.useForm()
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (values: { user_phone: string; product_category_id: string }) => {
    setLoading(true)
    try {
      await merchantService.admitSupplier(values)
      message.success('供应商准入成功')
      form.resetFields()
    } finally {
      setLoading(false)
    }
  }

  return (
    <Form form={form} layout="vertical" onFinish={handleSubmit} style={{ maxWidth: 400 }}>
      <Form.Item name="user_phone" label="供应商手机号" rules={[{ required: true }]}>
        <Input placeholder="供应商已注册的手机号" />
      </Form.Item>
      <Form.Item name="product_category_id" label="准入品类ID" rules={[{ required: true }]}>
        <Input placeholder="品类UUID" />
      </Form.Item>
      <Button type="primary" htmlType="submit" loading={loading}>准入供应商</Button>
    </Form>
  )
}

function DriverInviteForm() {
  const [form] = Form.useForm()
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (values: { user_phone: string }) => {
    setLoading(true)
    try {
      const res: { message: string; invite_code: string } = await merchantService.inviteDriver(values)
      message.success(`邀请码：${res.invite_code}，请发送给司机`)
      form.resetFields()
    } finally {
      setLoading(false)
    }
  }

  return (
    <Form form={form} layout="vertical" onFinish={handleSubmit} style={{ maxWidth: 400 }}>
      <Form.Item name="user_phone" label="司机手机号" rules={[{ required: true }]}>
        <Input placeholder="司机手机号" />
      </Form.Item>
      <Button type="primary" htmlType="submit" loading={loading}>生成邀请链接</Button>
    </Form>
  )
}

function KeeperAddForm() {
  const [form] = Form.useForm()
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (values: { user_phone: string }) => {
    setLoading(true)
    try {
      await merchantService.addWarehouseKeeper(values)
      message.success('仓管员已添加')
      form.resetFields()
    } finally {
      setLoading(false)
    }
  }

  return (
    <Form form={form} layout="vertical" onFinish={handleSubmit} style={{ maxWidth: 400 }}>
      <Form.Item name="user_phone" label="仓管员手机号" rules={[{ required: true }]}>
        <Input placeholder="仓管员已注册的手机号" />
      </Form.Item>
      <Button type="primary" htmlType="submit" loading={loading}>添加仓管员</Button>
    </Form>
  )
}

export default function TeamManagePage() {
  return (
    <Card title="团队管理">
      <Tabs
        items={[
          { key: 'supplier', label: '准入供应商', children: <SupplierAdmitForm /> },
          { key: 'driver', label: '邀请司机', children: <DriverInviteForm /> },
          { key: 'keeper', label: '添加仓管员', children: <KeeperAddForm /> },
        ]}
      />
    </Card>
  )
}
