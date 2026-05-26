/**
 * 统一 API 请求层
 * 与 Spring Boot 后端通信（开发环境通过 Vite proxy 代理到 8080）
 */

const BASE = '/api'

function getToken() {
  return localStorage.getItem('token') || ''
}

async function request(path, options = {}) {
  const { method = 'GET', body, silent = false } = options
  const headers = { 'Content-Type': 'application/json' }
  const token = getToken()
  if (token) headers['Authorization'] = 'Bearer ' + token

  try {
    const resp = await fetch(BASE + path, {
      method,
      headers,
      body: body ? JSON.stringify(body) : undefined,
    })
    if (!resp.ok) {
      if (!silent) alert(`服务器错误 (${resp.status})`)
      throw new Error(`HTTP ${resp.status}`)
    }
    const json = await resp.json()
    if (json.code === 200) return json.data
    if (!silent) alert(json.message || '请求失败')
    throw new Error(json.message || '请求失败')
  } catch (e) {
    if (!silent) alert('网络异常，请检查后端是否启动')
    throw e
  }
}

// ---- 导出业务 API ----
export const api = {
  recommend: (query, sessionId) =>
    request('/recommend', { method: 'POST', body: { user_query: query, sessionId, skipCache: false } }),
  qa: (question, sessionId) =>
    request('/qa', { method: 'POST', body: { question, sessionId } }),
  generateContent: (data) =>
    request('/content', { method: 'POST', body: data }),
  login: (code) =>
    request('/login', { method: 'POST', body: { code }, silent: true }),
  getUser: () => request('/user', { silent: true }),
  updateUser: (data) => request('/user', { method: 'PUT', body: data, silent: true }),
  getHistory: () => request('/user/history', { silent: true }),
  // 知识库（仅 Spring Boot 有，Flask 环境静默失败）
  getKnowledge: (params = {}) => {
    const qs = new URLSearchParams(params).toString()
    return request('/knowledge' + (qs ? '?' + qs : ''), { silent: true })
  },
  getKnowledgeById: (id) => request('/knowledge/' + id, { silent: true }),
  createKnowledge: (data) => request('/knowledge', { method: 'POST', body: data }),
  updateKnowledge: (id, data) => request('/knowledge/' + id, { method: 'PUT', body: data }),
  deleteKnowledge: (id) => request('/knowledge/' + id, { method: 'DELETE' }),
  // Prompt（仅 Spring Boot 有）
  getPrompts: (params = {}) => {
    const qs = new URLSearchParams(params).toString()
    return request('/prompt' + (qs ? '?' + qs : ''), { silent: true })
  },
  createPrompt: (data) => request('/prompt', { method: 'POST', body: data }),
  updatePrompt: (id, data) => request('/prompt/' + id, { method: 'PUT', body: data }),
  deletePrompt: (id) => request('/prompt/' + id, { method: 'DELETE' }),
  // 算法参数（仅 Spring Boot 有）
  getAlgoParams: (group) => {
    const qs = group ? '?group=' + group : ''
    return request('/algo-params' + qs, { silent: true })
  },
  updateAlgoParam: (id, data) => request('/algo-params/' + id, { method: 'PUT', body: data }),
}
