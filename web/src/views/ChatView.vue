<script setup>
import { ref, nextTick, onMounted, computed } from 'vue'
import { api } from '../api/request'
import PomeloCard from '../components/PomeloCard.vue'

const mode = ref('recommend')
const inputText = ref('')
const messages = ref([])
const loading = ref(false)
const abortController = ref(null)
const sessionId = ref('')
const sessionList = ref([])
const showHistory = ref(false)
const sendLock = ref(false)

const MAX_INPUT_LENGTH = 500
const DEBOUNCE_MS = 500
let debounceTimer = null

const HINTS = {
  recommend: '你好！我是AI导购 🍐\n告诉我你的需求，比如"200元送礼推荐"或"适合老人的水果"',
  qa: '你好！我是农产品知识专家 📚\n问我任何问题，比如"苹果怎么保存"或"沙田柚和蜜柚的区别"',
}

onMounted(async () => {
  const stored = localStorage.getItem('pomelo_session_id')
  if (stored) {
    sessionId.value = stored
    await loadHistory()
  } else {
    sessionId.value = 'web_' + Date.now().toString(36) + Math.random().toString(36).slice(2, 6)
    localStorage.setItem('pomelo_session_id', sessionId.value)
    messages.value.push({ role: 'ai', type: 'text', content: HINTS.recommend })
  }

  const q = localStorage.getItem('quick_query')
  if (q) {
    localStorage.removeItem('quick_query')
    const qMode = localStorage.getItem('quick_query_mode')
    localStorage.removeItem('quick_query_mode')
    if (qMode === 'qa') mode.value = 'qa'
    inputText.value = q
    nextTick(() => send())
  }
})

async function loadHistory() {
  try {
    const history = await api.getHistory(sessionId.value, 50)
    if (history && history.length > 0) {
      messages.value = history.map(m => ({
        id: m.id,
        role: m.role, type: m.msgType || 'text',
        content: m.content,
        items: m.metadataJson ? JSON.parse(m.metadataJson).items : undefined,
        feedback: undefined,
        fromHistory: true,
      }))
      return
    }
  } catch (e) { console.warn('加载历史失败:', e) }
  messages.value.push({ role: 'ai', type: 'text', content: HINTS.recommend })
}

function send() {
  if (sendLock.value || loading.value || !inputText.value.trim()) return
  if (inputText.value.length > MAX_INPUT_LENGTH) return

  // 防抖
  if (debounceTimer) clearTimeout(debounceTimer)
  sendLock.value = true
  debounceTimer = setTimeout(() => { sendLock.value = false }, DEBOUNCE_MS)

  doSend()
}

async function doSend() {
  const text = inputText.value.trim()
  inputText.value = ''
  loading.value = true

  const userMsg = { role: 'user', type: 'text', content: text }
  messages.value.push(userMsg)

  const loadingMsg = { role: 'ai', type: 'loading', content: '' }
  messages.value.push(loadingMsg)
  await nextTick(); scrollBottom()

  api.saveMessage({ sessionId: sessionId.value, role: 'user', msgType: 'text', content: text }).catch(() => {})

  try {
    await sendStream(text)
  } catch {
    messages.value = messages.value.filter(m => m.type !== 'loading')
    // 错误卡片 + 重试按钮
    messages.value.push({
      role: 'ai', type: 'error',
      content: '抱歉，出了一点问题 😥',
      retryText: text,
    })
  }

  loading.value = false
  abortController.value = null
  sendLock.value = false
  await nextTick(); scrollBottom()
}

async function sendStream(text) {
  const baseUrl = window.location.origin + '/api'
  const isQa = mode.value === 'qa'

  abortController.value = new AbortController()

  // 优先流式 SSE
  const streamEndpoint = isQa ? baseUrl + '/qa/stream' : baseUrl + '/recommend/stream'
  try {
    const resp = await fetch(streamEndpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ [isQa ? 'question' : 'user_query']: text, sessionId: sessionId.value }),
      signal: abortController.value.signal,
    })
    if (resp.ok && (resp.headers.get('content-type') || '').includes('text/event-stream')) {
      await handleSSE(resp, isQa)
      return
    }
  } catch (e) {
    if (e.name === 'AbortError') return
  }

  // 降级：非流式
  const endpoint = isQa ? baseUrl + '/qa' : baseUrl + '/recommend'
  const resp = await fetch(endpoint, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ [isQa ? 'question' : 'user_query']: text, sessionId: sessionId.value }),
    signal: abortController.value.signal,
  })
  if (!resp.ok) throw new Error('HTTP ' + resp.status)
  const json = await resp.json()
  handleResponse(json.code === 200 ? json.data : json, isQa)
}

async function handleSSE(resp, isQa) {
  const reader = resp.body.getReader()
  const decoder = new TextDecoder()
  let fullContent = ''
  let finalData = null

  messages.value = messages.value.filter(m => m.type !== 'loading')
  const aiIdx = messages.value.length
  messages.value.push({ role: 'ai', type: 'text', content: '' })

  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    const lines = decoder.decode(value, { stream: true }).split('\n')
    for (const line of lines) {
      if (!line.startsWith('data: ')) continue
      try {
        const evt = JSON.parse(line.substring(6))
        if (evt.event === 'done') { finalData = evt.data }
        else if (evt.event === 'token') {
          fullContent += evt.token
          if (aiIdx < messages.value.length) messages.value[aiIdx].content = fullContent
        }
      } catch {}
    }
    await nextTick(); scrollBottom()
  }

  messages.value.splice(aiIdx, 1)
  if (finalData) {
    handleStreamDone(finalData, isQa)
  } else if (fullContent) {
    messages.value.push({ role: 'ai', type: 'text', content: fullContent })
    api.saveMessage({ sessionId: sessionId.value, role: 'ai', msgType: 'text', content: fullContent }).catch(() => {})
  }
}

function handleStreamDone(data, isQa) {
  if (isQa) {
    const answer = data.answer || '抱歉，暂时无法回答。'
    messages.value.push({ role: 'ai', type: 'text', content: answer })
    api.saveMessage({ sessionId: sessionId.value, role: 'ai', msgType: 'text', content: answer }).catch(() => {})
  } else {
    const recs = data.recommendations || []
    if (recs.length > 0) {
      const summary = (data.intent?.intent || '') === 'BUY'
        ? 为您精选了  款产品：
        : 为您找到  款相关产品：
      const top3 = recs.slice(0, 3)
      messages.value.push({ role: 'ai', type: 'recommend', content: summary, items: top3 })
      api.saveMessage({ sessionId: sessionId.value, role: 'ai', msgType: 'recommend', content: summary,
        metadataJson: JSON.stringify({ items: top3, intent: data.intent }) }).catch(() => {})
    }
  }
}

function handleResponse(data, isQa) {
  messages.value = messages.value.filter(m => m.type !== 'loading')
  if (isQa) {
    const answer = data.answer || '抱歉，暂时无法回答。'
    const prefix = data.source === 'KNOWLEDGE_BASE' ? '📎 ' : '🤖 '
    const content = prefix + answer
    messages.value.push({ role: 'ai', type: 'text', content })
    api.saveMessage({ sessionId: sessionId.value, role: 'ai', msgType: 'text', content }).catch(() => {})
  } else {
    const recs = data.recommendations || []
    if (recs.length > 0) {
      const summary = (data.intent?.intent || '') === 'BUY'
        ? 为您精选了  款产品：
        : 为您找到  款相关产品：
      const top3 = recs.slice(0, 3)
      messages.value.push({ role: 'ai', type: 'recommend', content: summary, items: top3 })
      api.saveMessage({ sessionId: sessionId.value, role: 'ai', msgType: 'recommend', content: summary,
        metadataJson: JSON.stringify({ items: top3, intent: data.intent }) }).catch(() => {})
    } else if (data.answer) {
      messages.value.push({ role: 'ai', type: 'text', content: data.answer })
      api.saveMessage({ sessionId: sessionId.value, role: 'ai', msgType: 'text', content: data.answer }).catch(() => {})
    } else {
      messages.value.push({ role: 'ai', type: 'text', content: '抱歉，暂时没有找到合适的推荐，换个方式描述试试～' })
    }
  }
}

// 重试
function retry(msg) {
  inputText.value = msg.retryText
  nextTick(() => send())
}

// 反馈
function feedback(msg, type) {
  msg.feedback = msg.feedback === type ? null : type
}

// 停止
function stopGeneration() {
  if (abortController.value) { abortController.value.abort(); loading.value = false; sendLock.value = false }
  messages.value = messages.value.filter(m => m.type !== 'loading')
}

function newChat() {
  messages.value = []
  sessionId.value = 'web_' + Date.now().toString(36) + Math.random().toString(36).slice(2, 6)
  localStorage.setItem('pomelo_session_id', sessionId.value)
  mode.value = 'recommend'
  messages.value.push({ role: 'ai', type: 'text', content: HINTS.recommend })
}

async function toggleHistory() {
  showHistory.value = !showHistory.value
  if (showHistory.value && sessionList.value.length === 0) {
    const userId = JSON.parse(localStorage.getItem('user') || '{}').id
    if (userId) { try { sessionList.value = await api.getSessions(userId, 20) } catch { sessionList.value = [] } }
  }
}

async function switchSession(sid) {
  showHistory.value = false; sessionId.value = sid
  localStorage.setItem('pomelo_session_id', sid)
  messages.value = []; await loadHistory()
}

async function deleteCurrentSession() {
  if (!confirm('确认删除当前会话？')) return
  try { await api.deleteSession(sessionId.value) } catch {}
  newChat()
}

function switchMode(m) { mode.value = m; messages.value.push({ role: 'ai', type: 'text', content: HINTS[m] }); nextTick(() => scrollBottom()) }
function scrollBottom() { const el = document.querySelector('.chat-area'); if (el) el.scrollTop = el.scrollHeight }
const inputLength = computed(() => inputText.value.length)
const inputOverLimit = computed(() => inputLength.value > MAX_INPUT_LENGTH)
</script>

<template>
  <div class="chat-page">
    <!-- 顶栏 -->
    <div class="chat-header">
      <div class="mode-bar">
        <button :class="['mode-btn', { active: mode === 'recommend' }]" @click="switchMode('recommend')">🛒 选购推荐</button>
        <button :class="['mode-btn', { active: mode === 'qa' }]" @click="switchMode('qa')">📖 知识问答</button>
      </div>
      <div class="header-actions">
        <button class="icon-btn" title="历史" @click="toggleHistory">📋</button>
        <button class="icon-btn" title="新对话" @click="newChat">➕</button>
        <button class="icon-btn" title="删除" @click="deleteCurrentSession" v-if="messages.length > 1">🗑️</button>
      </div>
    </div>

    <!-- 历史面板 -->
    <transition name="slide">
      <div class="history-panel" v-if="showHistory">
        <div class="history-header">
          <span class="history-title">历史会话</span>
          <button class="btn-close" @click="showHistory = false">✕</button>
        </div>
        <div v-if="sessionList.length === 0" class="history-empty">暂无历史会话</div>
        <div v-for="s in sessionList" :key="s.session_id" class="history-item"
             :class="{ active: s.session_id === sessionId }" @click="switchSession(s.session_id)">
          <span class="history-id">{{ s.session_id?.slice(0, 14) }}...</span>
          <span class="history-meta">{{ s.msg_count }} 条</span>
        </div>
      </div>
    </transition>

    <!-- 聊天区 -->
    <div class="chat-area">
      <div v-for="(msg, i) in messages" :key="i">
        <!-- 用户消息 -->
        <div v-if="msg.role === 'user'" class="msg-row right">
          <div class="bubble user">{{ msg.content }}</div>
        </div>

        <!-- AI 文本 -->
        <div v-else-if="msg.type === 'text'" class="msg-row left">
          <div class="avatar">🍐</div>
          <div class="bubble ai" style="white-space: pre-wrap;">{{ msg.content }}</div>
          <!-- 反馈按钮 -->
          <div class="feedback-btns" v-if="!msg.fromHistory">
            <button :class="['fb-btn', { active: msg.feedback === 'up' }]" @click="feedback(msg, 'up')" title="有用">👍</button>
            <button :class="['fb-btn', { active: msg.feedback === 'down' }]" @click="feedback(msg, 'down')" title="无用">👎</button>
          </div>
        </div>

        <!-- AI 推荐卡片 -->
        <div v-else-if="msg.type === 'recommend'" class="msg-row left">
          <div class="avatar">🍐</div>
          <div class="bubble ai rec-bubble">
            <div class="rec-summary">{{ msg.content }}</div>
            <PomeloCard v-for="item in (msg.items || [])" :key="item.id" :item="item" :showScoring="true" />
          </div>
          <div class="feedback-btns" v-if="!msg.fromHistory">
            <button :class="['fb-btn', { active: msg.feedback === 'up' }]" @click="feedback(msg, 'up')">👍</button>
            <button :class="['fb-btn', { active: msg.feedback === 'down' }]" @click="feedback(msg, 'down')">👎</button>
          </div>
        </div>

        <!-- 错误卡片 -->
        <div v-else-if="msg.type === 'error'" class="msg-row left">
          <div class="avatar">😥</div>
          <div class="bubble ai error-bubble">
            <div class="error-content">
              <span>{{ msg.content }}</span>
              <button class="btn btn-sm btn-outline retry-btn" @click="retry(msg)">🔄 重试</button>
            </div>
          </div>
        </div>

        <!-- 加载 -->
        <div v-else-if="msg.type === 'loading'" class="msg-row left">
          <div class="avatar">🍐</div>
          <div class="bubble ai loading-bubble">
            <span class="dot">●</span><span class="dot">●</span><span class="dot">●</span>
            <span class="loading-tip">AI 正在思考...</span>
            <button class="stop-btn" @click="stopGeneration" v-if="loading">⏹ 停止</button>
          </div>
        </div>
      </div>
    </div>

    <!-- 输入区 -->
    <div class="input-bar">
      <input class="chat-input" v-model="inputText"
             :placeholder="mode === 'qa' ? '输入你的问题，如"苹果怎么保存"...' : '输入需求，如"200元送礼推荐水果"...'"
             :maxlength="MAX_INPUT_LENGTH"
             @keyup.enter="send" :disabled="loading" />
      <span class="char-count" :class="{ over: inputOverLimit }">{{ inputLength }}/{{ MAX_INPUT_LENGTH }}</span>
      <button class="btn btn-gold" @click="send" :disabled="loading || inputOverLimit || !inputText.trim()">发送</button>
    </div>
  </div>
</template>

<style scoped>
.chat-page { display: flex; flex-direction: column; height: calc(100vh - 136px); height: calc(100dvh - 136px); position: relative; }

/* === 顶栏 === */
.chat-header { display: flex; align-items: center; gap: 10px; margin-bottom: 12px; }
.mode-bar { flex: 1; display: flex; gap: 6px; background: var(--bg-card); border-radius: var(--radius-full); padding: 4px; border: 1px solid var(--border-light); }
.mode-btn { flex: 1; padding: 10px 14px; border-radius: var(--radius-full); border: none; background: transparent; cursor: pointer; font-size: 13px; font-weight: 600; color: var(--text-secondary); transition: all .25s var(--ease-out); }
.mode-btn.active { background: var(--primary); color: #fff; box-shadow: var(--shadow-button); }
.header-actions { display: flex; gap: 4px; }
.icon-btn { width: 36px; height: 36px; border-radius: 50%; border: 1px solid var(--border-light); background: var(--bg-card); cursor: pointer; font-size: 16px; display: flex; align-items: center; justify-content: center; transition: all .2s; }
.icon-btn:hover { background: var(--gold-light); border-color: var(--gold); }

/* === 历史面板 === */
.history-panel { position: absolute; top: 52px; left: 0; right: 0; background: var(--bg-card); border: 1px solid var(--border); border-radius: var(--radius-lg); padding: 16px; z-index: 10; max-height: 320px; overflow-y: auto; box-shadow: var(--shadow-md); }
.history-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.history-title { font-weight: 700; font-size: 14px; color: var(--text-primary); }
.btn-close { background: none; border: none; cursor: pointer; font-size: 16px; color: var(--text-placeholder); padding: 4px 8px; border-radius: var(--radius-xs); }
.btn-close:hover { background: var(--bg-warm); color: var(--text-primary); }
.history-empty { color: var(--text-placeholder); font-size: 13px; text-align: center; padding: 24px; }
.history-item { display: flex; justify-content: space-between; align-items: center; padding: 10px 14px; border-radius: var(--radius-sm); cursor: pointer; transition: background .15s; margin-bottom: 4px; }
.history-item:hover { background: var(--gold-light); }
.history-item.active { background: var(--gold-light); border: 1px solid var(--gold); }
.history-id { font-size: 13px; font-weight: 600; color: var(--text-primary); font-family: var(--font-mono); }
.history-meta { font-size: 11px; color: var(--text-placeholder); }

/* === 聊天区 === */
.chat-area { flex: 1; overflow-y: auto; padding: 4px 0; scroll-behavior: smooth; }
.msg-row { display: flex; margin-bottom: 18px; gap: 10px; animation: slideUp .35s var(--ease-out) both; align-items: flex-end; }
.msg-row.right { justify-content: flex-end; }
.msg-row.left { flex-wrap: wrap; }
.avatar { width: 36px; height: 36px; border-radius: 50%; background: var(--gold-light); display: flex; align-items: center; justify-content: center; font-size: 18px; flex-shrink: 0; box-shadow: var(--shadow-xs); }

.bubble { max-width: 75%; padding: 14px 18px; border-radius: var(--radius-lg); font-size: .9rem; line-height: 1.7; word-break: break-word; }
.bubble.user { background: linear-gradient(135deg, var(--primary), #e8746e); color: #fff; border-bottom-right-radius: var(--radius-xs); box-shadow: var(--shadow-button); }
.bubble.ai { background: var(--bg-card); border: 1px solid var(--border-light); border-bottom-left-radius: var(--radius-xs); box-shadow: var(--shadow-sm); }
.rec-bubble { max-width: 92%; padding: 16px; }
.rec-summary { font-weight: 700; margin-bottom: 12px; font-size: .92rem; }

/* 错误气泡 */
.error-bubble { border-color: rgba(217,80,74,.2); background: var(--primary-light); }
.error-content { display: flex; flex-direction: column; gap: 10px; align-items: flex-start; }
.retry-btn { align-self: flex-start; }

/* 加载气泡 */
.loading-bubble { display: flex; align-items: center; gap: 8px; padding: 14px 22px; }
.dot { width: 7px; height: 7px; border-radius: 50%; background: var(--primary); animation: dotBounce 1.4s infinite ease-in-out both; display: inline-block; }
.dot:nth-child(1) { animation-delay: 0s; }
.dot:nth-child(2) { animation-delay: .2s; }
.dot:nth-child(3) { animation-delay: .4s; }
.loading-tip { font-size: .8rem; color: var(--text-placeholder); margin-left: 4px; }
.stop-btn { margin-left: 12px; padding: 4px 12px; border-radius: var(--radius-full); border: 1.5px solid var(--accent); background: transparent; color: var(--accent); cursor: pointer; font-size: 12px; font-weight: 600; transition: all .15s; }
.stop-btn:hover { background: var(--accent); color: #fff; }

/* 反馈按钮 */
.feedback-btns { display: flex; gap: 4px; margin-left: 46px; margin-top: -6px; }
.fb-btn { width: 28px; height: 28px; border-radius: 50%; border: 1px solid var(--border-light); background: var(--bg-card); cursor: pointer; font-size: 13px; display: flex; align-items: center; justify-content: center; transition: all .15s; opacity: .5; }
.fb-btn:hover, .fb-btn.active { opacity: 1; border-color: var(--primary); background: var(--primary-light); }

/* === 输入区 === */
.input-bar { display: flex; align-items: center; gap: 10px; padding: 12px 0 8px; background: var(--bg-paper); }
.chat-input {
  flex: 1; padding: 14px 20px; border: 1.5px solid var(--border); border-radius: var(--radius-full);
  font-size: .9rem; outline: none; background: var(--bg-card); color: var(--text-primary);
  transition: all .2s; font-family: var(--font-body);
}
.chat-input:focus { border-color: var(--primary); box-shadow: 0 0 0 3px rgba(217,80,74,.08); }
.chat-input::placeholder { color: var(--text-placeholder); }
.char-count { font-size: 11px; color: var(--text-placeholder); min-width: 45px; text-align: right; }
.char-count.over { color: var(--accent); font-weight: 600; }

/* === Transitions === */
.slide-enter-active, .slide-leave-active { transition: all .25s var(--ease-out); }
.slide-enter-from, .slide-leave-to { opacity: 0; transform: translateY(-8px); }

@keyframes slideUp { from { opacity: 0; transform: translateY(12px); } to { opacity: 1; transform: translateY(0); } }
@keyframes dotBounce { 0%,80%,100% { transform: scale(0); } 40% { transform: scale(1); } }
</style>
