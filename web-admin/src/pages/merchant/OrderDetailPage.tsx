// v1.0 - 订单详情页（完整操作流：派车/过磅/入库/签章/支付）
import { useState, useEffect } from 'react'
import {
  Card, Descriptions, Button, Space, Tag, Modal, Form, Input,
  InputNumber, Select, message,
} from 'antd'
import { useParams, useNavigate } from 'react-router-dom'
import dayjs from 'dayjs'
import { merchantService } from '../../services/merchant'

interface Order {
  id: string; order_no: string; order_type: string; product_name: string
  quantity: number; unit_price: number; total_amount: number; status: string
  transport_arrangement: string; driver_id?: string; plate_no?: string
  created_at: string
}

const STATUS_LABEL: Record<string, string> = {
  DRAFT: '草稿', COMMITTED: '已认售', DISPATCHED: '已派车',
  ARRIVED_SOURCE: '到达货源地', SOURCE_WEIGHED: '货源过磅',
  IN_TRANSIT: '运输中', ARRIVED_WAREHOUSE: '到达仓库',
  WAREHOUSE_WEIGHED: '仓库过磅', WAREHOUSING: '入库中',
  WAREHOUSED: '已入库', CONTRACT_PENDING: '待签章',
  CONTRACTED: '已签章', PAYING: '支付中',
  PAID: '已付款', COMPLETED: '已完成', CANCELLED: '已取消',
}

export default function OrderDetailPage() {
  const { orderId } = useParams<{ orderId: string }>()
  const navigate = useNavigate()
  const [order, setOrder] = useState<Order | null>(null)
  const [loading, setLoading] = useState(false)
  const [dispatchOpen, setDispatchOpen] = useState(false)
  const [weighbridgeOpen, setWeighbridgeOpen] = useState(false)
  const [warehouseOpen, setWarehouseOpen] = useState(false)
  const [payOpen, setPayOpen] = useState(false)
  const [dispatchForm] = Form.useForm()
  const [weighbridgeForm] = Form.useForm()
  const [warehouseForm] = Form.useForm()

  const fetchOrder = async () => {
    if (!orderId) return
    setLoading(true)
    try {
      const data = await merchantService.getOrder(orderId)
      setOrder(data as Order)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { fetchOrder() }, [orderId])

  const handleDispatch = async (values: { driver_id: string; plate_no: string }) => {
    if (!orderId) return
    await merchantService.dispatchOrder(orderId, values)
    message.success('派车成功')
    setDispatchOpen(false)
    fetchOrder()
  }

  const handleWeighbridge = async (values: {
    record_type: string; gross_weight: number; tare_weight: number; deduction?: number
  }) => {
    if (!orderId) return
    await merchantService.recordWeighbridge(orderId, values)
    message.success('过磅数据已保存')
    setWeighbridgeOpen(false)
    fetchOrder()
  }

  const handleWarehousing = async (values: {
    warehouse_id: string; quantity: number; actual_weight: number; location?: string
  }) => {
    if (!orderId) return
    await merchantService.confirmWarehousing(orderId, values)
    message.success('入库确认成功')
    setWarehouseOpen(false)
    fetchOrder()
  }

  const handleSign = async () => {
    if (!orderId) return
    await merchantService.signContract(orderId)
    message.success('签章完成')
    fetchOrder()
  }

  const handlePay = async () => {
    if (!orderId) return
    await merchantService.payOrder(orderId, { channel: 'bank_transfer' })
    message.success('支付请求已提交')
    setPayOpen(false)
    fetchOrder()
  }

  if (!order) return <Card loading={loading} />

  const actionButtons = []
  if (order.status === 'COMMITTED') {
    actionButtons.push(
      <Button key="dispatch" type="primary" onClick={() => setDispatchOpen(true)}>派车</Button>
    )
  }
  if (['ARRIVED_SOURCE', 'ARRIVED_WAREHOUSE'].includes(order.status)) {
    actionButtons.push(
      <Button key="weigh" type="primary" onClick={() => setWeighbridgeOpen(true)}>录入过磅</Button>
    )
  }
  if (['WAREHOUSE_WEIGHED', 'ARRIVED_WAREHOUSE'].includes(order.status)) {
    actionButtons.push(
      <Button key="warehouse" onClick={() => setWarehouseOpen(true)}>确认入库</Button>
    )
  }
  if (order.status === 'CONTRACT_PENDING') {
    actionButtons.push(
      <Button key="sign" type="primary" onClick={handleSign}>签章确认</Button>
    )
  }
  if (order.status === 'CONTRACTED') {
    actionButtons.push(
      <Button key="pay" type="primary" onClick={() => setPayOpen(true)}>发起支付</Button>
    )
  }

  return (
    <Card
      title={`订单详情：${order.order_no}`}
      extra={
        <Space>
          {actionButtons}
          <Button onClick={() => navigate('/merchant/orders')}>返回列表</Button>
        </Space>
      }
      loading={loading}
    >
      <Descriptions bordered column={2}>
        <Descriptions.Item label="订单类型">
          {{ DIRECT: '直采', TRADE: '贸易', SUB: '子单' }[order.order_type] || order.order_type}
        </Descriptions.Item>
        <Descriptions.Item label="当前状态">
          <Tag color="blue">{STATUS_LABEL[order.status] || order.status}</Tag>
        </Descriptions.Item>
        <Descriptions.Item label="物资名称">{order.product_name}</Descriptions.Item>
        <Descriptions.Item label="采购数量">{order.quantity} 吨</Descriptions.Item>
        <Descriptions.Item label="单价">¥{order.unit_price}/吨</Descriptions.Item>
        <Descriptions.Item label="订单金额">¥{Number(order.total_amount).toLocaleString()}</Descriptions.Item>
        <Descriptions.Item label="运输安排">{order.transport_arrangement}</Descriptions.Item>
        <Descriptions.Item label="车牌号">{order.plate_no || '—'}</Descriptions.Item>
        <Descriptions.Item label="创建时间">
          {dayjs(order.created_at).format('YYYY-MM-DD HH:mm')}
        </Descriptions.Item>
      </Descriptions>

      {/* 派车弹窗 */}
      <Modal title="派车" open={dispatchOpen}
        onCancel={() => setDispatchOpen(false)} onOk={() => dispatchForm.submit()} okText="确认">
        <Form form={dispatchForm} layout="vertical" onFinish={handleDispatch}>
          <Form.Item name="driver_id" label="司机ID" rules={[{ required: true }]}>
            <Input placeholder="司机的用户UUID" />
          </Form.Item>
          <Form.Item name="plate_no" label="车牌号" rules={[{ required: true }]}>
            <Input placeholder="例：粤A12345" />
          </Form.Item>
        </Form>
      </Modal>

      {/* 过磅弹窗 */}
      <Modal title="录入过磅数据" open={weighbridgeOpen}
        onCancel={() => setWeighbridgeOpen(false)} onOk={() => weighbridgeForm.submit()} okText="保存">
        <Form form={weighbridgeForm} layout="vertical" onFinish={handleWeighbridge}>
          <Form.Item name="record_type" label="过磅类型" rules={[{ required: true }]}>
            <Select options={[
              { value: 'source', label: '货源地过磅' },
              { value: 'warehouse', label: '仓库过磅' },
            ]} />
          </Form.Item>
          <Form.Item name="gross_weight" label="毛重(吨)" rules={[{ required: true }]}>
            <InputNumber min={0} precision={3} style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="tare_weight" label="皮重(吨)" rules={[{ required: true }]}>
            <InputNumber min={0} precision={3} style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="deduction" label="扣杂(吨)">
            <InputNumber min={0} precision={3} style={{ width: '100%' }} />
          </Form.Item>
        </Form>
      </Modal>

      {/* 入库弹窗 */}
      <Modal title="确认入库" open={warehouseOpen}
        onCancel={() => setWarehouseOpen(false)} onOk={() => warehouseForm.submit()} okText="确认">
        <Form form={warehouseForm} layout="vertical" onFinish={handleWarehousing}>
          <Form.Item name="warehouse_id" label="仓库ID" rules={[{ required: true }]}>
            <Input placeholder="仓库UUID" />
          </Form.Item>
          <Form.Item name="actual_weight" label="实际重量(吨)" rules={[{ required: true }]}>
            <InputNumber min={0} precision={3} style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="quantity" label="入库数量" rules={[{ required: true }]}>
            <InputNumber min={0} precision={3} style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="location" label="库位">
            <Input placeholder="例：A-01-03" />
          </Form.Item>
        </Form>
      </Modal>

      {/* 支付确认弹窗 */}
      <Modal title="确认支付" open={payOpen}
        onCancel={() => setPayOpen(false)} onOk={handlePay} okText="确认支付" okButtonProps={{ type: 'primary' }}>
        <p>订单金额：<strong>¥{Number(order.total_amount).toLocaleString()}</strong></p>
        <p>支付方式：银行转账</p>
        <p>确认后将发起支付请求，请确认金额无误。</p>
      </Modal>
    </Card>
  )
}
