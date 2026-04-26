// v1.0 - 商户管理台布局（收购商C / 贸易商B 共用）
import { Layout, Menu, Button, Typography } from 'antd'
import {
  SoundOutlined, UnorderedListOutlined,
  TeamOutlined, LogoutOutlined, DashboardOutlined, AuditOutlined,
} from '@ant-design/icons'
import { Routes, Route, useNavigate, useLocation, Navigate } from 'react-router-dom'
import { useAuthStore } from '../../stores/auth'
import AnnouncementPage from './AnnouncementPage'
import OrderListPage from './OrderListPage'
import OrderDetailPage from './OrderDetailPage'
import BrokerTaskPage from './BrokerTaskPage'
import TeamManagePage from './TeamManagePage'

const { Sider, Header, Content } = Layout
const { Text } = Typography

const menuItems = [
  { key: '/merchant/dashboard', icon: <DashboardOutlined />, label: '控制台' },
  { key: '/merchant/announcements', icon: <SoundOutlined />, label: '采购公告' },
  { key: '/merchant/orders', icon: <UnorderedListOutlined />, label: '订单管理' },
  { key: '/merchant/broker-tasks', icon: <AuditOutlined />, label: '经纪人任务' },
  { key: '/merchant/team', icon: <TeamOutlined />, label: '团队管理' },
]

export default function MerchantLayout() {
  const navigate = useNavigate()
  const location = useLocation()
  const { logout } = useAuthStore()

  const currentKey = menuItems.find((item) =>
    location.pathname.startsWith(item.key),
  )?.key || '/merchant/dashboard'

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider width={220} style={{ background: '#fff', borderRight: '1px solid #f0f0f0' }}>
        <div style={{ padding: '20px 24px', borderBottom: '1px solid #f0f0f0' }}>
          <Text strong style={{ fontSize: 18, color: '#1677ff' }}>物采通商户台</Text>
        </div>
        <Menu
          mode="inline"
          selectedKeys={[currentKey]}
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
          <Button icon={<LogoutOutlined />} onClick={() => { logout(); navigate('/login') }} type="text">
            退出登录
          </Button>
        </Header>
        <Content style={{ padding: 24, background: '#f5f5f5' }}>
          <Routes>
            <Route path="dashboard" element={<div>欢迎使用物采通商户管理台</div>} />
            <Route path="announcements" element={<AnnouncementPage />} />
            <Route path="orders" element={<OrderListPage />} />
            <Route path="orders/:orderId" element={<OrderDetailPage />} />
            <Route path="broker-tasks" element={<BrokerTaskPage />} />
            <Route path="team" element={<TeamManagePage />} />
            <Route path="*" element={<Navigate to="dashboard" replace />} />
          </Routes>
        </Content>
      </Layout>
    </Layout>
  )
}
