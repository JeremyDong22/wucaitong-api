// v1.0 - 门户端 API 服务（供应商A / 经纪人 / 司机 / 仓管员）
const http = require('../utils/request')

module.exports = {
  // ── 认证 ──────────────────────────────────────────
  sendSms: (phone) => http.post('/auth/sms/send', { phone }),
  loginByPhone: (phone, sms_code) => http.post('/auth/login/phone', { phone, sms_code }),
  loginByWx: (code) => http.post('/auth/login/wx', { code }),

  // ── 供应商：公告和认售 ────────────────────────────
  listAnnouncements: () => http.get('/portal/announcements'),
  commitSupply: (announcementId, data) =>
    http.post(`/portal/announcements/${announcementId}/commit`, data),

  // ── 供应商：订单和签章 ────────────────────────────
  listMyOrders: () => http.get('/portal/orders'),
  signContract: (orderId) => http.post(`/portal/orders/${orderId}/contract/sign`),

  // ── 经纪人：任务管理 ──────────────────────────────
  listBrokerTasks: () => http.get('/portal/broker/tasks'),
  acceptBrokerTask: (taskId) => http.post(`/portal/broker/tasks/${taskId}/accept`),
  fillSupplier: (taskId, data) =>
    http.post(`/portal/broker/tasks/${taskId}/suppliers`, data),

  // ── 司机：GPS打卡 / 上传 ──────────────────────────
  gpsCheckin: (orderId, data) =>
    http.post(`/portal/driver/tasks/${orderId}/checkin`, data),
  uploadEvidence: (orderId, data) =>
    http.post(`/portal/driver/tasks/${orderId}/upload`, data),

  // ── 仓管员：入库任务 ──────────────────────────────
  listWarehouseTasks: () => http.get('/portal/warehouse/tasks'),
  confirmReceipt: (orderId, data) =>
    http.post(`/portal/warehouse/tasks/${orderId}/receipt`, data),
}
