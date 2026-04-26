// v1.1 - Axios HTTP 客户端（统一请求拦截 + Token 注入 + 错误处理）
// 响应拦截器直接返回 data，类型覆盖为 Promise<T>
import axios from 'axios'
import { message } from 'antd'

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8001/api/v1'

const http = axios.create({
  baseURL: BASE_URL,
  timeout: 15000,
})

// 请求拦截：注入 JWT Token
http.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// 响应拦截：解包 data，统一错误提示
http.interceptors.response.use(
  (res) => res.data,
  (error) => {
    const msg = error.response?.data?.detail || '请求失败，请稍后重试'
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      localStorage.removeItem('role')
      window.location.href = '/login'
    } else {
      message.error(msg)
    }
    return Promise.reject(error)
  },
)

// 导出类型安全的方法（返回 T 而非 AxiosResponse<T>）
const api = {
  get: <T = unknown>(url: string, config?: object): Promise<T> =>
    http.get(url, config) as unknown as Promise<T>,
  post: <T = unknown>(url: string, data?: unknown, config?: object): Promise<T> =>
    http.post(url, data, config) as unknown as Promise<T>,
  put: <T = unknown>(url: string, data?: unknown, config?: object): Promise<T> =>
    http.put(url, data, config) as unknown as Promise<T>,
  patch: <T = unknown>(url: string, data?: unknown, config?: object): Promise<T> =>
    http.patch(url, data, config) as unknown as Promise<T>,
  delete: <T = unknown>(url: string, config?: object): Promise<T> =>
    http.delete(url, config) as unknown as Promise<T>,
}

export default api
