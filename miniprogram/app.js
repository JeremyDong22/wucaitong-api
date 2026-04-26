// v1.0 - 物采通小程序入口（门户端：供应商A / 经纪人 / 司机 / 仓管员）
const { request } = require('./utils/request')

App({
  globalData: {
    token: '',
    role: '',
    userId: '',
    userInfo: null,
  },

  onLaunch() {
    // 读取本地缓存的登录态
    const token = wx.getStorageSync('token')
    const role = wx.getStorageSync('role')
    const userId = wx.getStorageSync('userId')
    if (token) {
      this.globalData.token = token
      this.globalData.role = role
      this.globalData.userId = userId
    }
  },

  // 全局登出
  logout() {
    wx.removeStorageSync('token')
    wx.removeStorageSync('role')
    wx.removeStorageSync('userId')
    this.globalData.token = ''
    this.globalData.role = ''
    this.globalData.userId = ''
    wx.reLaunch({ url: '/pages/login/login' })
  },
})
