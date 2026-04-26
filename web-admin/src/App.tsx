// v1.0 - 物采通管理台 App 根组件（基于角色路由）
import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuthStore } from './stores/auth'
import LoginPage from './pages/LoginPage'
import PlatformLayout from './pages/platform/PlatformLayout'
import MerchantLayout from './pages/merchant/MerchantLayout'

function App() {
  const { token, role } = useAuthStore()

  if (!token) {
    return (
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    )
  }

  // 平台管理员路由（PLATFORM_ADMIN）
  if (role === 'W') {
    return (
      <Routes>
        <Route path="/platform/*" element={<PlatformLayout />} />
        <Route path="*" element={<Navigate to="/platform/dashboard" replace />} />
      </Routes>
    )
  }

  // 商户路由（C / B）
  return (
    <Routes>
      <Route path="/merchant/*" element={<MerchantLayout />} />
      <Route path="*" element={<Navigate to="/merchant/dashboard" replace />} />
    </Routes>
  )
}

export default App
