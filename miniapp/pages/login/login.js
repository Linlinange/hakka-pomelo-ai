const { login } = require('../../utils/request');

Page({
  data: { loading: false },

  /** 微信授权登录 */
  onWxLogin() {
    if (this.data.loading) return;
    this.setData({ loading: true });

    wx.login({
      success: res => {
        if (!res.code) {
          wx.showToast({ title: '获取授权失败', icon: 'none' });
          this.setData({ loading: false });
          return;
        }

        // 获取用户信息（需用户授权）
        wx.getUserProfile({
          desc: '用于完善用户资料',
          success: profile => {
            const userInfo = profile.userInfo;
            login({
              code: res.code,
              nickname: userInfo.nickName,
              avatarUrl: userInfo.avatarUrl,
            })
              .then(data => {
                wx.setStorageSync('token', data.token);
                wx.setStorageSync('userId', data.userId);
                wx.setStorageSync('nickname', data.nickname);
                wx.setStorageSync('avatarUrl', data.avatarUrl);
                wx.showToast({ title: '登录成功', icon: 'success' });
                setTimeout(() => wx.switchTab({ url: '/pages/mine/mine' }), 1000);
              })
              .catch(err => {
                console.error('登录失败:', err);
                wx.showToast({ title: '登录失败，请重试', icon: 'none' });
              })
              .finally(() => this.setData({ loading: false }));
          },
          fail: () => {
            // 用户拒绝授权，仅用 code 登录
            login({ code: res.code })
              .then(data => {
                wx.setStorageSync('token', data.token);
                wx.setStorageSync('userId', data.userId);
                wx.setStorageSync('nickname', data.nickname || '');
                wx.showToast({ title: '登录成功', icon: 'success' });
                setTimeout(() => wx.switchTab({ url: '/pages/mine/mine' }), 800);
              })
              .catch(err => {
                wx.showToast({ title: '登录失败', icon: 'none' });
              })
              .finally(() => this.setData({ loading: false }));
          }
        });
      },
      fail: () => {
        wx.showToast({ title: '微信登录失败', icon: 'none' });
        this.setData({ loading: false });
      }
    });
  },

  /** 跳过登录 */
  onSkip() {
    wx.switchTab({ url: '/pages/index/index' });
  },
});
