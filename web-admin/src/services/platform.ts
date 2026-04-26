// v1.2 - 平台端 API 服务（品类管理 / 商户审核 / 商户绑定）
// 修复：createCategory 字段对齐后端 schema（category_code/category_name），
//       toggleCategoryStatus 改为 query param（?active=true）
import api from './http'

export const platformService = {
  listCategories: () => api.get<unknown[]>('/platform/products'),
  createCategory: (data: {
    category_code: string
    category_name: string
    unit: string
    sub_category?: string
    is_hazardous?: boolean
  }) => api.post('/platform/products', data),
  // 后端 active 是 query param，不是 body
  toggleCategoryStatus: (id: string, active: boolean) =>
    api.patch(`/platform/products/${id}/status?active=${active}`),

  listMerchants: (params?: { merchant_type?: string; status?: string }) =>
    api.get<unknown[]>('/platform/merchants', { params }),
  approveMerchant: (id: string, approved: boolean, reason?: string) =>
    api.post(`/platform/merchants/${id}/approve`, { approved, reason }),

  listRelations: () => api.get<unknown[]>('/platform/merchants/relations'),
  createRelation: (data: {
    upstream_merchant_id: string
    downstream_merchant_id: string
    product_category_id: string
  }) => api.post('/platform/merchants/relations', data),
  deleteRelation: (id: string) =>
    api.delete(`/platform/merchants/relations/${id}`),
}
