// v1.0 - 订单列表页（按状态筛选 + 点击查看详情）
import { useState, useEffect } from 'react'
import { Card, Table, Tag, Select, Button } from 'antd'
import { EyeOutlined } from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import dayjs from 'dayjs'
import { merchantService } from '../../services/merchant'

interface Order {
  id: string
  order_no: string
  order_type: string
  product_name: string
  quantity: number
  unit_price: number
  total_amount: number
  status: string
  created_at: string
}

// 订单状态中文映射
const STATUS_LABEL: Record<string, string> = {
  DRAFT: '草稿', COMMITTED: '已认售', DISPATCHED: '已派车',
  ARRIVED_SOURCE: '到达货源地', SOURCE_WEIGHED: '货源过磅',
  IN_TRANSIT: '运输中', ARRIVED_WAREHOUSE: '到达仓库',
  WAREHOUSE_WEIGHED: '仓库过磅', WAREHOUSING: '入库中',
  WAREHOUSED: '已入库', CONTRACT_PENDING: '待签章',
  CONTRACTED: '已签章', PAYING: '支付中',
  PAID: '已付款', COMPLETED: '已完成', CANCELLED: '已取消',
}

const STATUS_COLOR: Record<string, string> = {
  DRAFT: 'default', COMMITTED: 'blue', DISPATCHED: 'cyan',
  ARRIVED_SOURCE: 'geekblue', SOURCE_WEIGHED: 'purple',
  IN_TRANSIT: 'processing', ARRIVED_WAREHOUSE: 'volcano',
  WAREHOUSE_WEIGHED: 'orange', WAREHOUSING: 'gold',
  WAREHOUSED: 'lime', CONTRACT_PENDING: 'warning',
  CONTRACTED: 'green', PAYING: 'processing',
  PAID: 'success', COMPLETED: 'success', CANCELLED: 'error',
}

export default function OrderListPage() {
  const [orders, setOrders] = useState<Order[]>([])
  const [loading, setLoading] = useState(false)
  const [statusFilter, setStatusFilter] = useState<string>()
  const navigate = useNavigate()

  const fetchOrders = async () => {
    setLoading(true)
    try {
      const data = await merchantService.listOrders(statusFilter)
      setOrders(data as Order[])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { fetchOrders() }, [statusFilter])

  const columns = [
    { title: '订单号', dataIndex: 'order_no', key: 'no', width: 180 },
    {
      title: '类型', dataIndex: 'order_type', key: 'type', width: 90,
      render: (t: string) => {
        const map: Record<string, string> = { DIRECT: '直采', TRADE: '贸易', SUB: '子单' }
        return <Tag>{map[t] || t}</Tag>
      },
    },
    { title: '物资名称', dataIndex: 'product_name', key: 'product' },
    {
      title: '数量', dataIndex: 'quantity', key: 'qty', width: 100,
      render: (v: number) => `${v} 吨`,
    },
    {
      title: '金额', dataIndex: 'total_amount', key: 'amount', width: 120,
      render: (v: number) => `¥${Number(v).toLocaleString()}`,
    },
    {
      title: '状态', dataIndex: 'status', key: 'status', width: 110,
      render: (s: string) => (
        <Tag color={STATUS_COLOR[s]}>{STATUS_LABEL[s] || s}</Tag>
      ),
    },
    {
      title: '创建时间', dataIndex: 'created_at', key: 'created', width: 130,
      render: (v: string) => dayjs(v).format('MM-DD HH:mm'),
    },
    {
      title: '操作', key: 'action', width: 80,
      render: (_: unknown, record: Order) => (
        <Button
          size="small" icon={<EyeOutlined />}
          onClick={() => navigate(`/merchant/orders/${record.id}`)}
        >
          详情
        </Button>
      ),
    },
  ]

  return (
    <Card
      title="订单管理"
      extra={
        <Select
          placeholder="全部状态" allowClear style={{ width: 150 }}
          onChange={setStatusFilter}
          options={Object.entries(STATUS_LABEL).map(([v, l]) => ({ value: v, label: l }))}
        />
      }
    >
      <Table
        rowKey="id" columns={columns} dataSource={orders}
        loading={loading} pagination={{ pageSize: 20 }}
      />
    </Card>
  )
}
