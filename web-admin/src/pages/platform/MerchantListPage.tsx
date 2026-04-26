// v1.0 - 商户管理页（审核入驻申请）
import { useState, useEffect } from 'react'
import {
  Card, Table, Button, Tag, Modal, Input, message, Space, Select,
} from 'antd'
import { platformService } from '../../services/platform'

interface Merchant {
  id: string
  merchant_type: 'C' | 'B'
  company_name: string
  status: string
  credit_code: string
  contact_name: string
  contact_phone: string
  created_at: string
}

export default function MerchantListPage() {
  const [merchants, setMerchants] = useState<Merchant[]>([])
  const [loading, setLoading] = useState(false)
  const [rejectReason, setRejectReason] = useState('')
  const [rejectTarget, setRejectTarget] = useState<string | null>(null)
  const [typeFilter, setTypeFilter] = useState<string>()

  const fetchMerchants = async () => {
    setLoading(true)
    try {
      const data = await platformService.listMerchants(
        typeFilter ? { merchant_type: typeFilter } : undefined,
      )
      setMerchants(data as Merchant[])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { fetchMerchants() }, [typeFilter])

  const handleApprove = async (id: string) => {
    try {
      await platformService.approveMerchant(id, true)
      message.success('已审核通过')
      fetchMerchants()
    } catch {}
  }

  const handleReject = async () => {
    if (!rejectTarget) return
    try {
      await platformService.approveMerchant(rejectTarget, false, rejectReason)
      message.success('已拒绝')
      setRejectTarget(null)
      setRejectReason('')
      fetchMerchants()
    } catch {}
  }

  const statusColor: Record<string, string> = {
    pending: 'orange', active: 'green', rejected: 'red', suspended: 'gray',
  }
  const statusLabel: Record<string, string> = {
    pending: '待审核', active: '已通过', rejected: '已拒绝', suspended: '已暂停',
  }

  const columns = [
    {
      title: '类型', dataIndex: 'merchant_type', key: 'type', width: 80,
      render: (t: string) => <Tag color={t === 'C' ? 'blue' : 'purple'}>{t === 'C' ? '收购商' : '贸易商'}</Tag>,
    },
    { title: '公司名称', dataIndex: 'company_name', key: 'company' },
    { title: '联系人', dataIndex: 'contact_name', key: 'contact', width: 100 },
    { title: '联系电话', dataIndex: 'contact_phone', key: 'phone', width: 130 },
    {
      title: '状态', dataIndex: 'status', key: 'status', width: 90,
      render: (s: string) => <Tag color={statusColor[s]}>{statusLabel[s] || s}</Tag>,
    },
    {
      title: '操作', key: 'action', width: 160,
      render: (_: unknown, record: Merchant) =>
        record.status === 'pending' ? (
          <Space>
            <Button type="primary" size="small" onClick={() => handleApprove(record.id)}>通过</Button>
            <Button danger size="small" onClick={() => setRejectTarget(record.id)}>拒绝</Button>
          </Space>
        ) : '—',
    },
  ]

  return (
    <Card
      title="商户管理"
      extra={
        <Select
          placeholder="全部类型" allowClear style={{ width: 120 }}
          onChange={setTypeFilter}
          options={[
            { value: 'C', label: '收购商' },
            { value: 'B', label: '贸易商' },
          ]}
        />
      }
    >
      <Table
        rowKey="id" columns={columns} dataSource={merchants}
        loading={loading} pagination={{ pageSize: 20 }}
      />
      <Modal
        title="拒绝原因"
        open={!!rejectTarget}
        onOk={handleReject}
        onCancel={() => { setRejectTarget(null); setRejectReason('') }}
        okText="确认拒绝"
        okButtonProps={{ danger: true }}
      >
        <Input.TextArea
          rows={3}
          placeholder="请填写拒绝原因（可选）"
          value={rejectReason}
          onChange={(e) => setRejectReason(e.target.value)}
        />
      </Modal>
    </Card>
  )
}
