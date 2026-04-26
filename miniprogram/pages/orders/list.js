// v1.0 - 订单列表（供应商视角）
const portalService = require('../../services/portal')

const STATUS_LABEL = {
  DRAFT: '草稿', COMMITTED: '已认售', DISPATCHED: '已派车',
  ARRIVED_SOURCE: '到达货源地', SOURCE_WEIGHED: '货源过磅',
  IN_TRANSIT: '运输中', ARRIVED_WAREHOUSE: '到达仓库',
  WAREHOUSE_WEIGHED: '仓库过磅', WAREHOUSING: '入库中',
  WAREHOUSED: '已入库', CONTRACT_PENDING: '待签章',
  CONTRACTED: '已签章', PAYING: '支付中',
  PAID: '已付款', COMPLETED: '已完成', CANCELLED: '已取消',
}

Page({
  data: {
    orders: [],
    loading: false,
  },

  onShow() {
    this.loadData()
  },

  async loadData() {
    this.setData({ loading: true })
    try {
      const list = await portalService.listMyOrders()
      const orders = list.map((o) => ({
        ...o,
        statusLabel: STATUS_LABEL[o.status] || o.status,
      }))
      this.setData({ orders })
    } finally {
      this.setData({ loading: false })
    }
  },

  onPullDownRefresh() {
    this.loadData().then(() => wx.stopPullDownRefresh())
  },

  goDetail(e) {
    const { id } = e.currentTarget.dataset
    wx.navigateTo({ url: `/pages/orders/detail?id=${id}` })
  },
})
