// v1.0 - 订单详情（供应商签章操作）
const portalService = require('../../services/portal')

Page({
  data: {
    orderId: '',
    order: null,
    signing: false,
  },

  onLoad(options) {
    this.setData({ orderId: options.id })
  },

  onShow() {
    // 订单详情暂无单独接口，从列表中获取
    // 实际应添加 GET /portal/orders/{id} 接口
  },

  async signContract() {
    const { orderId } = this.data
    this.setData({ signing: true })
    try {
      await portalService.signContract(orderId)
      wx.showToast({ title: '签章完成', icon: 'success' })
      setTimeout(() => wx.navigateBack(), 1500)
    } finally {
      this.setData({ signing: false })
    }
  },
})
