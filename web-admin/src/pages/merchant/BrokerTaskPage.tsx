// v1.0 - 经纪人任务页（创建/查看代采任务）
import { useState, useEffect } from 'react'
import {
  Card, Table, Button, Modal, Form, Input, InputNumber, DatePicker, Tag, message,
} from 'antd'
import { PlusOutlined } from '@ant-design/icons'
import dayjs from 'dayjs'
import { merchantService } from '../../services/merchant'

interface BrokerTask {
  id: string; task_no: string; product_name: string; quantity: number
  unit_price: number; deadline: string; status: string
}

const STATUS_LABEL: Record<string, string> = {
  pending: '待接受', accepted: '已接受', processing: '处理中', completed: '已完成', cancelled: '已取消',
}

export default function BrokerTaskPage() {
  const [tasks, setTasks] = useState<BrokerTask[]>([])
  const [loading, setLoading] = useState(false)
  const [createOpen, setCreateOpen] = useState(false)
  const [form] = Form.useForm()

  const fetchTasks = async () => {
    setLoading(true)
    try {
      const data = await merchantService.listBrokerTasks()
      setTasks(data as BrokerTask[])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { fetchTasks() }, [])

  const handleCreate = async (values: {
    broker_id: string; product_name: string; quantity: number; unit_price: number; deadline: dayjs.Dayjs
  }) => {
    try {
      await merchantService.createBrokerTask({
        ...values,
        deadline: values.deadline.toISOString(),
        product_category_id: null,
      })
      message.success('任务已创建')
      setCreateOpen(false)
      form.resetFields()
      fetchTasks()
    } catch {}
  }

  const columns = [
    { title: '任务编号', dataIndex: 'task_no', key: 'no', width: 160 },
    { title: '物资名称', dataIndex: 'product_name', key: 'product' },
    { title: '数量(吨)', dataIndex: 'quantity', key: 'qty', width: 100 },
    {
      title: '单价', dataIndex: 'unit_price', key: 'price', width: 110,
      render: (v: number) => `¥${v}/吨`,
    },
    {
      title: '截止时间', dataIndex: 'deadline', key: 'deadline', width: 130,
      render: (v: string) => dayjs(v).format('MM-DD HH:mm'),
    },
    {
      title: '状态', dataIndex: 'status', key: 'status', width: 90,
      render: (s: string) => <Tag>{STATUS_LABEL[s] || s}</Tag>,
    },
  ]

  return (
    <Card
      title="经纪人代采任务"
      extra={
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setCreateOpen(true)}>
          创建任务
        </Button>
      }
    >
      <Table
        rowKey="id" columns={columns} dataSource={tasks}
        loading={loading} pagination={{ pageSize: 20 }}
      />
      <Modal
        title="创建经纪人任务"
        open={createOpen}
        onCancel={() => { setCreateOpen(false); form.resetFields() }}
        onOk={() => form.submit()}
        okText="创建"
        width={520}
      >
        <Form form={form} layout="vertical" onFinish={handleCreate}>
          <Form.Item name="broker_id" label="经纪人ID" rules={[{ required: true }]}>
            <Input placeholder="经纪人的UUID" />
          </Form.Item>
          <Form.Item name="product_name" label="物资名称" rules={[{ required: true }]}>
            <Input placeholder="例：废旧铜" />
          </Form.Item>
          <Form.Item name="quantity" label="目标数量(吨)" rules={[{ required: true }]}>
            <InputNumber min={0} precision={3} style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="unit_price" label="参考单价(元/吨)" rules={[{ required: true }]}>
            <InputNumber min={0} precision={2} style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="deadline" label="截止时间" rules={[{ required: true }]}>
            <DatePicker showTime style={{ width: '100%' }} />
          </Form.Item>
        </Form>
      </Modal>
    </Card>
  )
}
