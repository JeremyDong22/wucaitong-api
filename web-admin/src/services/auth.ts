// v1.1 - 认证 API 服务（手机登录 / 发送短信）
import api from './http'

export interface LoginResponse {
  access_token: string
  token_type: string
  role: string
  user_id: string
}

export const authService = {
  sendSms: (phone: string) =>
    api.post<{ message: string; debug_code?: string }>('/auth/sms/send', { phone }),

  loginByPhone: (phone: string, sms_code: string): Promise<LoginResponse> =>
    api.post<LoginResponse>('/auth/login/phone', { phone, sms_code }),
}
