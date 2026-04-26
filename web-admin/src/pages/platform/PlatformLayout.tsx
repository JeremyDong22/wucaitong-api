// v1.0 - 平台管理台布局（左侧导航 + 内容区）
import { Layout, Menu, Button, Typography } from 'antd'
import {
  AppstoreOutlined, TeamOutlined, LinkOutlined, LogoutOutlined, DashboardOutlined,
} from '@ant-design/icons'
import { Routes, Route, useNavigate, useLocation, Navigate } from 'react-router-dom'
import { useAuthStore } from '../../stores/auth'
import ProductCategoryPage from './ProductCategoryPage'
import MerchantListPage from './MerchantListPage'
import MerchantRelationPage from './MerchantRelationPage'

const { Sider, Header, Content } = Layout
const { Text } = Typography

const menuItems = [
  { key: '/platform/dashboard', icon: <DashboardOutlined />, label: '控制台' },
  { key: '/platform/categories', icon: <AppstoreOutlined />, label: '品类管理' },
  { key: '/platform/merchants', icon: <TeamOutlined />, label: '商户管理' },
  { key: '/platform/relations', icon: <LinkOutlined />, label: '商户绑定' },
]

export default function PlatformLayout() {
  const navigate = useNavigate()
  const location = useLocation()
  const { logout } = useAuthStore()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider width={220} style={{ background: '#fff', borderRight: '1px solid #f0f0f0' }}>
        <div style={{ padding: '20px 24px', borderBottom: '1px solid #f0f0f0' }}>
          <Text strong style={{ fontSize: 18, color: '#1677ff' }}>物采通平台</Text>
        </div>
        <Menu
          mode="inline"
          selectedKeys={[location.pathname]}
          items={menuItems}
          onClick={({ key }) => navigate(key)}
          style={{ border: 'none', marginTop: 8 }}
        />
      </Sider>
      <Layout>
        <Header style={{
          background: '#fff', padding: '0 24px',
          borderBottom: '1px solid #f0f0f0',
          display: 'flex', alignItems: 'center', justifyContent: 'flex-end',
        }}>
          <Button icon={<LogoutOutlined />} onClick={handleLogout} type="text">退出登录</Button>
        </Header>
        <Content style={{ padding: 24, background: '#f5f5f5' }}>
          <Routes>
            <Route path="dashboard" element={<div>欢迎使用物采通平台管理台</div>} />
            <Route path="categories" element={<ProductCategoryPage />} />
            <Route path="merchants" element={<MerchantListPage />} />
            <Route path="relations" element={<MerchantRelationPage />} />
            <Route path="*" element={<Navigate to="dashboard" replace />} />
          </Routes>
        </Content>
      </Layout>
    </Layout>
  )
}
