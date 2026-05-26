/**
 * 客家金柚AI智荐 - 微信小程序入口
 *
 * 部署时修改 apiBaseUrl：
 *   开发环境: http://127.0.0.1:8080
 *   生产环境: https://your-domain.com
 */
App({
  globalData: {
    userInfo: null,
    token: '',
    apiBaseUrl: 'http://127.0.0.1:8080',
  },

  onLaunch() {
    const token = wx.getStorageSync('token');
    if (!token) {
      this._wxLogin();
    }
  },

  _wxLogin() {
    wx.login({
      success: res => {
        if (res.code) {
          wx.request({
            url: this.globalData.apiBaseUrl + '/api/login',
            method: 'POST',
            data: { code: res.code },
            success: resp => {
              if (resp.statusCode === 200 && resp.data && resp.data.token) {
                wx.setStorageSync('token', resp.data.token);
              }
              // demo 模式下 /api/login 返回 500 是正常的（无微信AppID），静默跳过
            },
            fail: () => {
              // 网络不通时静默跳过，不影响浏览
            }
          });
        }
      },
      fail: () => {}
    });
  },
});
