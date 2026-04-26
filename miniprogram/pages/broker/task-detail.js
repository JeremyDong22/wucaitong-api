// v1.0 - 经纪人代填供应商信息
const portalService = require('../../services/portal')

Page({
  data: {
    taskId: '',
    supplierPhone: '',
    quantity: '',
    deliveryDate: '',
    submitting: false,
  },

  onLoad(options) {
    this.setData({ taskId: options.id })
  },

  onPhoneInput(e) { this.setData({ supplierPhone: e.detail.value }) },
  onQuantityInput(e) { this.setData({ quantity: e.detail.value }) },
  onDateChange(e) { this.setData({ deliveryDate: e.detail.value }) },

  async submit() {
    const { taskId, supplierPhone, quantity, deliveryDate } = this.data
    if (!supplierPhone || !quantity) {
      wx.showToast({ title: '请填写手机号和数量', icon: 'none' })
      return
    }
    this.setData({ submitting: true })
    try {
      await portalService.fillSupplier(taskId, {
        supplier_phone: supplierPhone,
        quantity: Number(quantity),
        expected_delivery_date: deliveryDate || null,
      })
      wx.showToast({ title: '供应商信息已提交', icon: 'success' })
      setTimeout(() => wx.navigateBack(), 1500)
    } finally {
      this.setData({ submitting: false })
    }
  },
})
