const { get, getUserProfile } = require('../../utils/request');

Page({
  data: {
    isLogin: false,
    nickname: '',
    avatarUrl: '',
    userId: '',
    historyList: [],
  },

  onShow() {
    const token = wx.getStorageSync('token');
    if (token) {
      this.setData({
        isLogin: true,
        nickname: wx.getStorageSync('nickname') || '水果爱好者',
        avatarUrl: wx.getStorageSync('avatarUrl') || '',
        userId: String(wx.getStorageSync('userId') || ''),
      });
      this.loadHistory();
    } else {
      this.setData({ isLogin: false, historyList: [] });
    }
  },

  loadHistory() {
    get('/user/history')
      .then(data => this.setData({ historyList: (data || []).slice(0, 10) }))
      .catch(() => {});
  },

  goLogin() {
    wx.navigateTo({ url: '/pages/login/login' });
  },

  goAdmin() {
    wx.navigateTo({ url: '/pages/admin/admin' });
  },

  /** 点击历史记录，跳转AI智荐 */
  onQuickAsk(e) {
    const text = e.currentTarget.dataset.text;
    wx.setStorageSync('quick_query', text);
    wx.switchTab({ url: '/pages/recommend/recommend' });
  },

  /** 退出登录 */
  onLogout() {
    wx.showModal({
      title: '确认退出',
      content: '退出后需要重新登录',
      success: res => {
        if (res.confirm) {
          wx.removeStorageSync('token');
          wx.removeStorageSync('userId');
          wx.removeStorageSync('nickname');
          wx.removeStorageSync('avatarUrl');
          this.setData({ isLogin: false, nickname: '', avatarUrl: '', userId: '' });
          wx.showToast({ title: '已退出', icon: 'none' });
        }
      }
    });
  },
});
