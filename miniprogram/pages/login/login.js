// v1.0 - 登录页（手机号+短信验证码 / 微信OAuth）
const portalService = require('../../services/portal')

Page({
  data: {
    phone: '',
    code: '',
    countdown: 0,
    smsSent: false,
    loading: false,
  },

  // 发送短信验证码
  async sendSms() {
    const { phone } = this.data
    if (!phone || phone.length !== 11) {
      wx.showToast({ title: '请输入正确的手机号', icon: 'none' })
      return
    }
    try {
      await portalService.sendSms(phone)
      wx.showToast({ title: '验证码已发送', icon: 'success' })
      this.setData({ smsSent: true, countdown: 60 })
      const timer = setInterval(() => {
        const c = this.data.countdown - 1
        if (c <= 0) { clearInterval(timer); this.setData({ countdown: 0 }) }
        else { this.setData({ countdown: c }) }
      }, 1000)
    } catch {}
  },

  // 手机号登录
  async loginByPhone() {
    const { phone, code } = this.data
    if (!phone || !code) {
      wx.showToast({ title: '请填写手机号和验证码', icon: 'none' })
      return
    }
    this.setData({ loading: true })
    try {
      const res = await portalService.loginByPhone(phone, code)
      this._saveLoginState(res)
    } finally {
      this.setData({ loading: false })
    }
  },

  // 微信登录
  async loginByWx() {
    try {
      const { code } = await new Promise((resolve, reject) =>
        wx.login({ success: resolve, fail: reject }),
      )
      const res = await portalService.loginByWx(code)
      this._saveLoginState(res)
    } catch {}
  },

  _saveLoginState(res) {
    wx.setStorageSync('token', res.access_token)
    wx.setStorageSync('role', res.role)
    wx.setStorageSync('userId', res.user_id)
    const app = getApp()
    app.globalData.token = res.access_token
    app.globalData.role = res.role
    app.globalData.userId = res.user_id
    wx.switchTab({ url: '/pages/index/index' })
  },

  onPhoneInput(e) { this.setData({ phone: e.detail.value }) },
  onCodeInput(e) { this.setData({ code: e.detail.value }) },
})
