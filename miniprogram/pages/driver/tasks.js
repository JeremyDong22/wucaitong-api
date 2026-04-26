// v1.0 - 司机任务页（GPS打卡 / 上传磅单照片）
const portalService = require('../../services/portal')

Page({
  data: {
    orderId: '',
    checkingIn: false,
    uploading: false,
  },

  onLoad(options) {
    if (options.orderId) {
      this.setData({ orderId: options.orderId })
    }
  },

  // GPS打卡
  async checkin(e) {
    const { type } = e.currentTarget.dataset
    const { orderId } = this.data
    if (!orderId) {
      wx.showToast({ title: '请先输入订单ID', icon: 'none' })
      return
    }

    this.setData({ checkingIn: true })
    try {
      // 获取当前位置
      const location = await new Promise((resolve, reject) =>
        wx.getLocation({ type: 'gcj02', success: resolve, fail: reject }),
      )
      await portalService.gpsCheckin(orderId, {
        checkpoint_type: type,
        latitude: location.latitude,
        longitude: location.longitude,
      })
      const labelMap = {
        depart: '出发打卡', arrive_source: '到达货源地打卡', arrive_warehouse: '到达仓库打卡',
      }
      wx.showToast({ title: `${labelMap[type]}成功`, icon: 'success' })
    } finally {
      this.setData({ checkingIn: false })
    }
  },

  // 上传磅单照片
  async uploadEvidence() {
    const { orderId } = this.data
    if (!orderId) {
      wx.showToast({ title: '请先输入订单ID', icon: 'none' })
      return
    }

    try {
      const { tempFilePaths } = await new Promise((resolve, reject) =>
        wx.chooseMedia({
          count: 1, mediaType: ['image'],
          success: resolve, fail: reject,
        }),
      )
      this.setData({ uploading: true })
      // 实际应先上传到OSS获取URL，这里模拟
      const ossUrl = `https://dev-mock.oss.com/${Date.now()}.jpg`
      await portalService.uploadEvidence(orderId, {
        related_type: 'weighbridge',
        file_type: 'image',
        oss_url: ossUrl,
      })
      wx.showToast({ title: '上传成功', icon: 'success' })
    } finally {
      this.setData({ uploading: false })
    }
  },

  onOrderIdInput(e) {
    this.setData({ orderId: e.detail.value })
  },
})
