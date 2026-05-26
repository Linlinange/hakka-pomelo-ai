const { get } = require('../../utils/request');

Page({
  data: {
    id: '',
    entity: null,
    loading: true,
  },

  onLoad(options) {
    const id = options.id;
    if (!id) {
      wx.showToast({ title: '参数错误', icon: 'none' });
      return;
    }
    this.setData({ id });
    this.fetchDetail(id);
  },

  fetchDetail(id) {
    get('/knowledge/' + id)
      .then(data => {
        this.setData({ entity: data, loading: false });
      })
      .catch(() => {
        // 如果 API 不可用，用传递的参数
        const pages = getCurrentPages();
        // fallback: show error
        wx.showToast({ title: '获取详情失败', icon: 'none' });
        this.setData({ loading: false });
      });
  },

  /** 返回到推荐页提问 */
  onAskAbout() {
    const e = this.data.entity;
    if (e && e.pomeloName) {
      wx.setStorageSync('quick_query', '帮我介绍一下' + e.pomeloName);
      wx.switchTab({ url: '/pages/recommend/recommend' });
    }
  },

  onBack() {
    wx.navigateBack();
  },
});
