// v1.0 - 经纪人任务列表（接受任务 / 代填供应商）
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
      const list = await portalService.listBrokerTasks()
      this.setData({ tasks: list })
    } finally {
      this.setData({ loading: false })
    }
  },

  onPullDownRefresh() {
    this.loadData().then(() => wx.stopPullDownRefresh())
  },

  async acceptTask(e) {
    const { id } = e.currentTarget.dataset
    try {
      await portalService.acceptBrokerTask(id)
      wx.showToast({ title: '任务已接受', icon: 'success' })
      this.loadData()
    } catch {}
  },

  goDetail(e) {
    const { id } = e.currentTarget.dataset
    wx.navigateTo({ url: `/pages/broker/task-detail?id=${id}` })
  },
})
