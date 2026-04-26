// v1.0 - 小程序网络请求封装（统一 BaseURL + Token 注入 + 错误提示）
const BASE_URL = 'http://localhost:8001/api/v1'

const request = (method, url, data = {}) => {
  return new Promise((resolve, reject) => {
    const app = getApp()
    const token = app.globalData.token || wx.getStorageSync('token')

    wx.request({
      url: BASE_URL + url,
      method: method.toUpperCase(),
      data,
      header: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      success(res) {
        if (res.statusCode === 200 || res.statusCode === 201) {
          resolve(res.data)
        } else if (res.statusCode === 401) {
          wx.showToast({ title: '请重新登录', icon: 'none' })
          getApp().logout()
          reject(res.data)
        } else {
          const msg = res.data?.detail || '请求失败'
          wx.showToast({ title: msg, icon: 'none' })
          reject(res.data)
        }
      },
      fail(err) {
        wx.showToast({ title: '网络错误，请稍后重试', icon: 'none' })
        reject(err)
      },
    })
  })
}

module.exports = {
  get: (url, params) => {
    const query = params ? '?' + Object.entries(params).map(([k, v]) => `${k}=${v}`).join('&') : ''
    return request('GET', url + query)
  },
  post: (url, data) => request('POST', url, data),
  patch: (url, data) => request('PATCH', url, data),
  delete: (url) => request('DELETE', url),
}
