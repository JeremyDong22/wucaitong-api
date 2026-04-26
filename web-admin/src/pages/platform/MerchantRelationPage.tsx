// v1.0 - 商户绑定页（C-B 按品类绑定关系管理）
import { useState, useEffect } from 'react'
import {
  Card, Table, Button, Modal, Form, Select, message, Popconfirm, Tag,
} from 'antd'
import { PlusOutlined, DeleteOutlined } from '@ant-design/icons'
import { platformService } from '../../services/platform'

interface Relation {
  id: string
  upstream_merchant_id: string
  downstream_merchant_id: string
  product_category_id: string
  status: string
  upstream_name?: string
  downstream_name?: string
  category_name?: string
}

interface Merchant { id: string; company_name: string; merchant_type: string }
interface Category { id: string; name: string }

export default function MerchantRelationPage() {
  const [relations, setRelations] = useState<Relation[]>([])
  const [merchants, setMerchants] = useState<Merchant[]>([])
  const [categories, setCategories] = useState<Category[]>([])
  const [loading, setLoading] = useState(false)
  const [modalOpen, setModalOpen] = useState(false)
  const [form] = Form.useForm()

  const fetchAll = async () => {
    setLoading(true)
    try {
      const [rels, cats, mercs] = await Promise.all([
        platformService.listRelations(),
        platformService.listCategories(),
        platformService.listMerchants({ status: 'active' }),
      ])
      setRelations(rels as Relation[])
      setCategories(cats as Category[])
      setMerchants(mercs as Merchant[])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { fetchAll() }, [])

  const handleCreate = async (values: {
    upstream_merchant_id: string
    downstream_merchant_id: string
    product_category_id: string
  }) => {
    try {
      await platformService.createRelation(values)
      message.success('绑定关系创建成功')
      setModalOpen(false)
      form.resetFields()
      fetchAll()
    } catch {}
  }

  const handleDelete = async (id: string) => {
    try {
      await platformService.deleteRelation(id)
      message.success('已解除绑定')
      fetchAll()
    } catch {}
  }

  const merchantMap = Object.fromEntries(merchants.map((m) => [m.id, m]))
  const categoryMap = Object.fromEntries(categories.map((c) => [c.id, c]))

  const columns = [
    {
      title: '收购商(C)', dataIndex: 'upstream_merchant_id', key: 'upstream',
      render: (id: string) => merchantMap[id]?.company_name || id,
    },
    {
      title: '贸易商(B)', dataIndex: 'downstream_merchant_id', key: 'downstream',
      render: (id: string) => merchantMap[id]?.company_name || id,
    },
    {
      title: '品类', dataIndex: 'product_category_id', key: 'category',
      render: (id: string) => <Tag>{categoryMap[id]?.name || id}</Tag>,
    },
    { title: '状态', dataIndex: 'status', key: 'status', width: 80 },
    {
      title: '操作', key: 'action', width: 80,
      render: (_: unknown, record: Relation) => (
        <Popconfirm
          title="确认解除绑定？"
          onConfirm={() => handleDelete(record.id)}
          okText="确认" cancelText="取消"
        >
          <Button danger size="small" icon={<DeleteOutlined />}>解除</Button>
        </Popconfirm>
      ),
    },
  ]

  const cMerchants = merchants.filter((m) => m.merchant_type === 'C')
  const bMerchants = merchants.filter((m) => m.merchant_type === 'B')

  return (
    <Card
      title="商户绑定（C-B）"
      extra={
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setModalOpen(true)}>
          新增绑定
        </Button>
      }
    >
      <Table
        rowKey="id" columns={columns} dataSource={relations}
        loading={loading} pagination={{ pageSize: 20 }}
      />
      <Modal
        title="新增绑定关系"
        open={modalOpen}
        onCancel={() => { setModalOpen(false); form.resetFields() }}
        onOk={() => form.submit()}
        okText="创建"
      >
        <Form form={form} layout="vertical" onFinish={handleCreate}>
          <Form.Item name="upstream_merchant_id" label="收购商 (C)" rules={[{ required: true }]}>
            <Select
              placeholder="选择收购商"
              options={cMerchants.map((m) => ({ value: m.id, label: m.company_name }))}
            />
          </Form.Item>
          <Form.Item name="downstream_merchant_id" label="贸易商 (B)" rules={[{ required: true }]}>
            <Select
              placeholder="选择贸易商"
              options={bMerchants.map((m) => ({ value: m.id, label: m.company_name }))}
            />
          </Form.Item>
          <Form.Item name="product_category_id" label="品类" rules={[{ required: true }]}>
            <Select
              placeholder="选择品类"
              options={categories.map((c) => ({ value: c.id, label: c.name }))}
            />
          </Form.Item>
        </Form>
      </Modal>
    </Card>
  )
}
