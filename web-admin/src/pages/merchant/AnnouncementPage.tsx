// v1.0 - 采购公告页（发布公告 / 查看认售 / 确认认售）
import { useState, useEffect } from 'react'
import {
  Card, Table, Button, Modal, Form, Input, InputNumber,
  DatePicker, Select, message, Tag, Space,
} from 'antd'
import { PlusOutlined } from '@ant-design/icons'
import dayjs from 'dayjs'
import { merchantService } from '../../services/merchant'

interface Announcement {
  id: string
  product_name: string
  quantity: number
  remaining_quantity: number
  unit_price: number
  deadline: string
  status: string
  transport_arrangement: string
}

export default function AnnouncementPage() {
  const [announcements, setAnnouncements] = useState<Announcement[]>([])
  const [loading, setLoading] = useState(false)
  const [createOpen, setCreateOpen] = useState(false)
  const [form] = Form.useForm()

  const fetchData = async () => {
    setLoading(true)
    try {
      const data = await merchantService.listAnnouncements()
      setAnnouncements(data as Announcement[])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { fetchData() }, [])

  const handleCreate = async (values: {
    product_name: string
    quantity: number
    unit_price: number
    deadline: dayjs.Dayjs
    transport_arrangement: string
    specification?: string
    grade?: string
  }) => {
    try {
      await merchantService.createAnnouncement({
        ...values,
        deadline: values.deadline.toISOString(),
        product_category_id: null, // 暂无品类选择器
      })
      message.success('公告已发布')
      setCreateOpen(false)
      form.resetFields()
      fetchData()
    } catch {}
  }

  const statusColor: Record<string, string> = {
    active: 'green', closed: 'default', draft: 'orange',
  }

  const columns = [
    { title: '物资名称', dataIndex: 'product_name', key: 'name' },
    {
      title: '公告数量', dataIndex: 'quantity', key: 'qty',
      render: (v: number) => `${v} 吨`,
    },
    {
      title: '剩余数量', dataIndex: 'remaining_quantity', key: 'remaining',
      render: (v: number) => `${v} 吨`,
    },
    {
      title: '单价', dataIndex: 'unit_price', key: 'price',
      render: (v: number) => `¥${v}/吨`,
    },
    {
      title: '截止时间', dataIndex: 'deadline', key: 'deadline',
      render: (v: string) => dayjs(v).format('MM-DD HH:mm'),
    },
    {
      title: '状态', dataIndex: 'status', key: 'status', width: 90,
      render: (s: string) => <Tag color={statusColor[s]}>{s === 'active' ? '进行中' : s === 'closed' ? '已关闭' : '草稿'}</Tag>,
    },
  ]

  return (
    <Card
      title="采购公告"
      extra={
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setCreateOpen(true)}>
          发布公告
        </Button>
      }
    >
      <Table
        rowKey="id" columns={columns} dataSource={announcements}
        loading={loading} pagination={{ pageSize: 20 }}
      />
      <Modal
        title="发布采购公告"
        open={createOpen}
        onCancel={() => { setCreateOpen(false); form.resetFields() }}
        onOk={() => form.submit()}
        okText="发布"
        width={560}
      >
        <Form form={form} layout="vertical" onFinish={handleCreate}>
          <Form.Item name="product_name" label="物资名称" rules={[{ required: true }]}>
            <Input placeholder="例：废旧钢铁" />
          </Form.Item>
          <Space size={16} style={{ width: '100%' }}>
            <Form.Item name="quantity" label="采购数量(吨)" rules={[{ required: true }]} style={{ flex: 1 }}>
              <InputNumber min={0} precision={3} style={{ width: '100%' }} />
            </Form.Item>
            <Form.Item name="unit_price" label="单价(元/吨)" rules={[{ required: true }]} style={{ flex: 1 }}>
              <InputNumber min={0} precision={2} style={{ width: '100%' }} />
            </Form.Item>
          </Space>
          <Form.Item name="deadline" label="截止时间" rules={[{ required: true }]}>
            <DatePicker showTime style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="transport_arrangement" label="运输方式" rules={[{ required: true }]}>
            <Select options={[
              { value: 'buyer', label: '收购商安排运输' },
              { value: 'seller', label: '供应商自送' },
              { value: 'third_party', label: '第三方物流' },
            ]} />
          </Form.Item>
          <Form.Item name="specification" label="规格说明">
            <Input.TextArea rows={2} />
          </Form.Item>
        </Form>
      </Modal>
    </Card>
  )
}
