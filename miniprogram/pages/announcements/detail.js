// v1.0 - 公告详情+认售页
const portalService = require('../../services/portal')

Page({
  data: {
    id: '',
    quantity: '',
    deliveryDate: '',
    submitting: false,
  },

  onLoad(options) {
    this.setData({ id: options.id })
  },

  onQuantityInput(e) { this.setData({ quantity: e.detail.value }) },
  onDateChange(e) { this.setData({ deliveryDate: e.detail.value }) },

  async submitCommit() {
    const { id, quantity, deliveryDate } = this.data
    if (!quantity || Number(quantity) <= 0) {
      wx.showToast({ title: '请填写认售数量', icon: 'none' })
      return
    }
    this.setData({ submitting: true })
    try {
      await portalService.commitSupply(id, {
        quantity: Number(quantity),
        expected_delivery_date: deliveryDate || null,
      })
      wx.showToast({ title: '认售已提交', icon: 'success' })
      setTimeout(() => wx.navigateBack(), 1500)
    } finally {
      this.setData({ submitting: false })
    }
  },
})
