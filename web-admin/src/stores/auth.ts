// v1.0 - 认证状态管理（Zustand），持久化到 localStorage
import { create } from 'zustand'

interface AuthState {
  token: string | null
  role: string | null
  userId: string | null
  setAuth: (token: string, role: string, userId: string) => void
  logout: () => void
}

export const useAuthStore = create<AuthState>((set) => ({
  token: localStorage.getItem('token'),
  role: localStorage.getItem('role'),
  userId: localStorage.getItem('userId'),

  setAuth: (token, role, userId) => {
    localStorage.setItem('token', token)
    localStorage.setItem('role', role)
    localStorage.setItem('userId', userId)
    set({ token, role, userId })
  },

  logout: () => {
    localStorage.removeItem('token')
    localStorage.removeItem('role')
    localStorage.removeItem('userId')
    set({ token: null, role: null, userId: null })
  },
}))
