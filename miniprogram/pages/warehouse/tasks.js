// v1.0 - 仓管员入库任务列表
const portalService = require('../../services/portal')

Page({
  data: {
    tasks: [],
    loading: false,
  },

  onShow() {
    this.loadData()
  },

  async loadData() {
    this.setData({ loading: true })
    try {
      const list = await portalService.listWarehouseTasks()
      this.setData({ tasks: list })
    } finally {
      this.setData({ loading: false })
    }
  },

  onPullDownRefresh() {
    this.loadData().then(() => wx.stopPullDownRefresh())
  },

  goReceipt(e) {
    const { id } = e.currentTarget.dataset
    wx.navigateTo({ url: `/pages/warehouse/receipt?orderId=${id}` })
  },
})
