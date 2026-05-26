/**
 * 客家金柚AI智荐 - 微信小程序入口
 */
App({
  onLaunch() {
    // 获取用户本地 Token，若无则走微信登录流程
    const token = wx.getStorageSync('token');
    if (!token) {
      this._wxLogin();
    }
  },

  _wxLogin() {
    wx.login({
      success: res => {
        if (res.code) {
          // 将 code 发送到后端换取 openid 和 token
          wx.request({
            url: 'http://127.0.0.1:8080/api/login',
            method: 'POST',
            data: { code: res.code },
            success: resp => {
              if (resp.data && resp.data.token) {
                wx.setStorageSync('token', resp.data.token);
              }
            },
          });
        }
      }
    });
  },

  globalData: {
    userInfo: null,
    token: '',
  }
});
