// v1.0 - 首页（按角色显示对应功能入口）
Page({
  data: {
    role: '',
    menuItems: [],
  },

  onShow() {
    const app = getApp()
    const role = app.globalData.role || wx.getStorageSync('role')

    // 未登录跳转
    if (!role) {
      wx.reLaunch({ url: '/pages/login/login' })
      return
    }

    // 按角色配置菜单
    const menuMap = {
      A: [
        { title: '查看公告', icon: '📢', path: '/pages/announcements/list' },
        { title: '我的订单', icon: '📋', path: '/pages/orders/list' },
      ],
      BROKER: [
        { title: '代采任务', icon: '🤝', path: '/pages/broker/tasks' },
      ],
      DRIVER: [
        { title: '运输任务', icon: '🚛', path: '/pages/driver/tasks' },
      ],
      WAREHOUSE_KEEPER: [
        { title: '入库任务', icon: '🏭', path: '/pages/warehouse/tasks' },
      ],
    }

    this.setData({
      role,
      menuItems: menuMap[role] || [],
    })
  },

  navigateTo(e) {
    const { path } = e.currentTarget.dataset
    wx.navigateTo({ url: path })
  },

  logout() {
    wx.showModal({
      title: '确认退出',
      content: '退出登录后需重新验证',
      success: (res) => {
        if (res.confirm) getApp().logout()
      },
    })
  },
})
