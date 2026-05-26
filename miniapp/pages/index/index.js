/** 首页 — 功能入口导航 */
Page({
  data: {
    userInfo: null,
  },

  onShow() {
    const token = wx.getStorageSync('token');
    const nickname = wx.getStorageSync('nickname') || '';
    const avatar = wx.getStorageSync('avatarUrl') || '';
    this.setData({ userInfo: token ? { nickname, avatarUrl: avatar } : null });
  },

  // 跳转 AI 智荐
  goRecommend() {
    wx.switchTab({ url: '/pages/recommend/recommend' });
  },

  // 跳转文案生成
  goContent() {
    wx.switchTab({ url: '/pages/content/content' });
  },

  // 跳转登录/个人中心
  goMine() {
    const token = wx.getStorageSync('token');
    if (token) {
      wx.switchTab({ url: '/pages/mine/mine' });
    } else {
      wx.navigateTo({ url: '/pages/login/login' });
    }
  },

  // 跳转管理后台
  goAdmin() {
    wx.navigateTo({ url: '/pages/admin/admin' });
  },

  // 快捷提问 → AI智荐
  onQuickAsk(e) {
    const q = e.currentTarget.dataset.q;
    wx.setStorageSync('quick_query', q);
    wx.switchTab({ url: '/pages/recommend/recommend' });
  },
});
