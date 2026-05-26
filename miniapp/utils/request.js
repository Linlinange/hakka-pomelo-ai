/**
 * 统一网络请求层
 * - 自动注入 Token
 * - 统一异常提示
 * - 请求/响应日志
 */

function getBaseUrl() {
  const app = getApp();
  return (app.globalData.apiBaseUrl || 'http://127.0.0.1:8080') + '/api';
}

// 获取存储的 Token（微信登录后由 App.js 写入）
function getToken() {
  try {
    return wx.getStorageSync('token') || '';
  } catch (e) {
    return '';
  }
}

/**
 * 发起 POST 请求
 * @param {string} path    接口路径，如 '/recommend'
 * @param {object} data    请求体
 * @param {object} options 可选配置 { showLoading, loadingText, silent }
 * @returns {Promise<any>}
 */
function post(path, data = {}, options = {}) {
  const {
    showLoading = false,
    loadingText = '加载中...',
    silent = false, // true 时不弹错误 toast
  } = options;

  if (showLoading) {
    wx.showLoading({ title: loadingText, mask: true });
  }

  return new Promise((resolve, reject) => {
    wx.request({
      url: getBaseUrl() + path,
      method: 'POST',
      header: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + getToken(),
      },
      data: data,
      timeout: 30000,
      success(res) {
        if (res.statusCode === 200) {
          const body = res.data;
          if (body.code === 200) {
            resolve(body.data);
          } else {
            if (!silent) {
              wx.showToast({ title: body.message || '请求失败', icon: 'none' });
            }
            reject(new Error(body.message || '请求失败'));
          }
        } else if (res.statusCode === 401) {
          wx.showToast({ title: '登录已过期，请重新登录', icon: 'none' });
          reject(new Error('未授权'));
        } else {
          if (!silent) {
            wx.showToast({ title: '服务器繁忙 (' + res.statusCode + ')', icon: 'none' });
          }
          reject(new Error('HTTP ' + res.statusCode));
        }
      },
      fail(err) {
        if (!silent) {
          wx.showToast({ title: '网络异常，请检查连接', icon: 'none' });
        }
        reject(err);
      },
      complete() {
        if (showLoading) {
          wx.hideLoading();
        }
      }
    });
  });
}

/**
 * 推荐接口
 * @param {string} query      用户输入
 * @param {string} sessionId  会话ID
 */
function recommend(query, sessionId) {
  return post('/recommend', {
    query: query,
    sessionId: sessionId,
    skipCache: false,
  });
}

/**
 * 问答接口
 * @param {string} question   用户问题
 * @param {string} sessionId  会话ID
 */
function qa(question, sessionId) {
  return post('/qa', {
    question: question,
    sessionId: sessionId,
  });
}

// ---- GET 请求 ----
function get(path, params = {}) {
  const qs = Object.keys(params)
    .filter(k => params[k] !== undefined && params[k] !== null && params[k] !== '')
    .map(k => k + '=' + encodeURIComponent(params[k]))
    .join('&');
  const url = getBaseUrl() + path + (qs ? '?' + qs : '');
  return new Promise((resolve, reject) => {
    wx.request({
      url,
      method: 'GET',
      header: {
        'Authorization': 'Bearer ' + getToken(),
      },
      timeout: 15000,
      success(res) {
        if (res.statusCode === 200 && res.data.code === 200) {
          resolve(res.data.data);
        } else {
          reject(new Error(res.data.message || '请求失败'));
        }
      },
      fail: reject,
    });
  });
}

// ---- PUT 请求 ----
function put(path, data = {}) {
  return new Promise((resolve, reject) => {
    wx.request({
      url: getBaseUrl() + path,
      method: 'PUT',
      header: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + getToken(),
      },
      data,
      timeout: 15000,
      success(res) {
        if (res.statusCode === 200 && res.data.code === 200) {
          resolve(res.data.data);
        } else {
          reject(new Error(res.data.message || '请求失败'));
        }
      },
      fail: reject,
    });
  });
}

// ---- DELETE 请求 ----
function del(path) {
  return new Promise((resolve, reject) => {
    wx.request({
      url: getBaseUrl() + path,
      method: 'DELETE',
      header: {
        'Authorization': 'Bearer ' + getToken(),
      },
      timeout: 15000,
      success(res) {
        if (res.statusCode === 200 && res.data.code === 200) {
          resolve(res.data.data);
        } else {
          reject(new Error(res.data.message || '请求失败'));
        }
      },
      fail: reject,
    });
  });
}

// ---- 业务 API ----

/** 微信登录 */
function login(data) {
  return post('/login', data);
}

/** 获取用户信息 */
function getUserProfile() {
  return get('/user');
}

/** 更新用户信息 */
function updateUserProfile(data) {
  return put('/user', data);
}

/** 内容生成 */
function generateContent(data) {
  return post('/content', data);
}

module.exports = {
  get,
  post,
  put,
  del,
  recommend,
  qa,
  login,
  getUserProfile,
  updateUserProfile,
  generateContent,
};
