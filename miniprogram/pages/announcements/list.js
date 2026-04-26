// v1.0 - 采购公告列表（供应商认售入口）
const portalService = require('../../services/portal')

Page({
  data: {
    announcements: [],
    loading: false,
  },

  onShow() {
    this.loadData()
  },

  async loadData() {
    this.setData({ loading: true })
    try {
      const list = await portalService.listAnnouncements()
      this.setData({ announcements: list })
    } finally {
      this.setData({ loading: false })
    }
  },

  onPullDownRefresh() {
    this.loadData().then(() => wx.stopPullDownRefresh())
  },

  goDetail(e) {
    const { id } = e.currentTarget.dataset
    wx.navigateTo({ url: `/pages/announcements/detail?id=${id}` })
  },
})
