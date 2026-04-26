// v1.0 - 仓管员入库签章页
const portalService = require('../../services/portal')

Page({
  data: {
    orderId: '',
    submitting: false,
  },

  onLoad(options) {
    this.setData({ orderId: options.orderId })
  },

  async confirm() {
    const { orderId } = this.data
    this.setData({ submitting: true })
    try {
      await portalService.confirmReceipt(orderId, {
        receipt_id: orderId, // 简化：实际应从 warehouse_receipts 查询 receipt_id
      })
      wx.showToast({ title: '入库验收完成', icon: 'success' })
      setTimeout(() => wx.navigateBack(), 1500)
    } finally {
      this.setData({ submitting: false })
    }
  },
})
