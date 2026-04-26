// v1.1 - 商户端 API 服务（公告 / 订单 / 经纪人 / 人员）
import api from './http'

export const merchantService = {
  listAnnouncements: () => api.get<unknown[]>('/merchant/announcements'),
  createAnnouncement: (data: object) => api.post('/merchant/announcements', data),
  confirmCommitment: (announcementId: string, data: {
    commitment_id: string; approved: boolean
  }) => api.post(`/merchant/announcements/${announcementId}/confirm`, data),

  listOrders: (status?: string) =>
    api.get<unknown[]>('/merchant/orders', { params: status ? { order_status: status } : {} }),
  getOrder: (id: string) => api.get<unknown>(`/merchant/orders/${id}`),
  dispatchOrder: (id: string, data: { driver_id: string; plate_no: string }) =>
    api.post(`/merchant/orders/${id}/dispatch`, data),
  recordWeighbridge: (id: string, data: object) =>
    api.post(`/merchant/orders/${id}/weighbridge`, data),
  confirmWarehousing: (id: string, data: object) =>
    api.post(`/merchant/orders/${id}/warehouse`, data),
  signContract: (id: string) =>
    api.post(`/merchant/orders/${id}/contract/sign`),
  payOrder: (id: string, data: { channel: string }) =>
    api.post(`/merchant/orders/${id}/pay`, data),

  listBrokerTasks: () => api.get<unknown[]>('/merchant/broker-tasks'),
  createBrokerTask: (data: object) => api.post('/merchant/broker-tasks', data),

  admitSupplier: (data: { user_phone: string; product_category_id: string }) =>
    api.post<unknown>('/merchant/suppliers', data),
  inviteDriver: (data: { user_phone: string }) =>
    api.post<{ message: string; invite_code: string }>('/merchant/drivers', data),
  addWarehouseKeeper: (data: { user_phone: string }) =>
    api.post('/merchant/warehouse-keepers', data),
}
