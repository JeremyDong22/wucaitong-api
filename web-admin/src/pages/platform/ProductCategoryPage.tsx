// v1.1 - 品种字典管理页（对齐后端 ProductCategoryResponse schema）
// 修复：category_code / category_name 字段，status 替代 enabled，toggle 用 active query param
import { useState, useEffect } from 'react'
import {
  Card, Table, Button, Modal, Form, Input, Switch, Tag, message, Select,
} from 'antd'
import { PlusOutlined } from '@ant-design/icons'
import { platformService } from '../../services/platform'

// 对应后端 ProductCategoryResponse
interface ProductCategory {
  id: string
  category_code: string
  category_name: string
  unit: string
  status: 'active' | 'inactive'
}

// 常用计量单位
const UNIT_OPTIONS = [
  { value: 'ton', label: '吨' },
  { value: 'kg', label: '千克' },
  { value: 'piece', label: '件' },
  { value: 'set', label: '套' },
]

export default function ProductCategoryPage() {
  const [categories, setCategories] = useState<ProductCategory[]>([])
  const [loading, setLoading] = useState(false)
  const [modalOpen, setModalOpen] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [form] = Form.useForm()

  const fetchCategories = async () => {
    setLoading(true)
    try {
      const data = await platformService.listCategories()
      setCategories(data as ProductCategory[])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { fetchCategories() }, [])

  const handleCreate = async (values: {
    category_code: string
    category_name: string
    unit: string
    sub_category?: string
    is_hazardous?: boolean
  }) => {
    setSubmitting(true)
    try {
      await platformService.createCategory(values)
      message.success('品种创建成功')
      setModalOpen(false)
      form.resetFields()
      fetchCategories()
    } catch {
      // http 拦截器已提示错误
    } finally {
      setSubmitting(false)
    }
  }

  const handleToggle = async (record: ProductCategory) => {
    const toActive = record.status !== 'active'
    try {
      await platformService.toggleCategoryStatus(record.id, toActive)
      fetchCategories()
    } catch {}
  }

  const columns = [
    { title: '品种代码', dataIndex: 'category_code', key: 'category_code', width: 120 },
    { title: '品种名称', dataIndex: 'category_name', key: 'category_name' },
    { title: '单位', dataIndex: 'unit', key: 'unit', width: 100 },
    {
      title: '状态', dataIndex: 'status', key: 'status', width: 100,
      render: (status: string) => (
        <Tag color={status === 'active' ? 'green' : 'red'}>
          {status === 'active' ? '启用' : '停用'}
        </Tag>
      ),
    },
    {
      title: '操作', key: 'action', width: 100,
      render: (_: unknown, record: ProductCategory) => (
        <Switch
          checked={record.status === 'active'}
          onChange={() => handleToggle(record)}
          checkedChildren="启用" unCheckedChildren="停用"
        />
      ),
    },
  ]

  return (
    <Card
      title="品种字典"
      extra={
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setModalOpen(true)}>
          新增品种
        </Button>
      }
    >
      <Table
        rowKey="id" columns={columns} dataSource={categories}
        loading={loading} pagination={{ pageSize: 20 }}
      />

      <Modal
        title="新增废旧物资品种"
        open={modalOpen}
        onCancel={() => { setModalOpen(false); form.resetFields() }}
        onOk={() => form.submit()}
        okText="创建"
        confirmLoading={submitting}
      >
        <Form form={form} layout="vertical" onFinish={handleCreate}>
          <Form.Item
            name="category_code"
            label="品种代码"
            rules={[{ required: true, message: '请输入品种代码' }, { max: 20 }]}
          >
            <Input placeholder="例：STEEL、COPPER、ALUMINUM" style={{ textTransform: 'uppercase' }} />
          </Form.Item>
          <Form.Item
            name="category_name"
            label="品种名称"
            rules={[{ required: true, message: '请输入品种名称' }]}
          >
            <Input placeholder="例：废旧钢铁" />
          </Form.Item>
          <Form.Item
            name="unit"
            label="计量单位"
            initialValue="ton"
            rules={[{ required: true }]}
          >
            <Select options={UNIT_OPTIONS} placeholder="选择单位" />
          </Form.Item>
          <Form.Item name="sub_category" label="子类说明（可选）">
            <Input placeholder="例：生铁/熟铁/钢筋/废钢" />
          </Form.Item>
          <Form.Item name="is_hazardous" label="危废品种" valuePropName="checked" initialValue={false}>
            <Switch checkedChildren="是" unCheckedChildren="否" />
          </Form.Item>
        </Form>
      </Modal>
    </Card>
  )
}
