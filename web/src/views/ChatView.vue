<script setup>
import { ref, nextTick, onMounted } from 'vue'
import { api } from '../api/request'
import PomeloCard from '../components/PomeloCard.vue'

const mode = ref('recommend') // 'recommend' | 'qa'
const inputText = ref('')
const messages = ref([])
const loading = ref(false)
const sessionId = ref('web_' + Date.now().toString(36))

const HINTS = {
  recommend: '我是客家金柚AI导购～\n告诉我你的需求，比如"200元中秋送礼推荐"或"适合老人的金柚"',
  qa: '我是客家金柚知识专家～\n问我任何金柚相关的问题，比如"金柚怎么保存"或"沙田柚和蜜柚的区别"',
}

onMounted(() => {
  messages.value.push({ role: 'ai', type: 'text', content: HINTS.recommend })
  // 快捷提问 — 带模式跳转
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

async function send() {
  const text = inputText.value.trim()
  if (!text || loading.value) return
  messages.value.push({ role: 'user', type: 'text', content: text })
  inputText.value = ''
  loading.value = true
  messages.value.push({ role: 'ai', type: 'loading' })
  await nextTick(); scrollBottom()

  try {
    const apiCall = mode.value === 'qa' ? api.qa(text, sessionId.value) : api.recommend(text, sessionId.value)
    const data = await apiCall
    messages.value = messages.value.filter(m => m.type !== 'loading')
    if (mode.value === 'qa') {
      const answer = data.answer || '抱歉，暂时无法回答。'
      const prefix = data.source === 'KNOWLEDGE_BASE' ? '📚 ' : '🤖 '
      messages.value.push({ role: 'ai', type: 'text', content: prefix + answer })
    } else {
      const recs = data.recommendations || []
      // 如果有推荐列表 → 展示金柚卡片
      if (recs.length > 0) {
        const intentObj = data.intent || {}
        const summary = intentObj.intent === 'BUY'
          ? `为您精选了 ${recs.length} 款客家金柚：`
          : `为您找到 ${recs.length} 款相关金柚：`
        messages.value.push({ role: 'ai', type: 'recommend', content: summary, items: recs.slice(0, 3) })
      } else if (data.answer) {
        // 无候选金柚时，展示 LLM 自由对话回答
        messages.value.push({ role: 'ai', type: 'text', content: data.answer })
      } else {
        messages.value.push({ role: 'ai', type: 'text', content: '抱歉，暂时没有找到合适的推荐，换个方式描述试试～' })
      }
    }
  } catch {
    messages.value = messages.value.filter(m => m.type !== 'loading')
    messages.value.push({ role: 'ai', type: 'text', content: '抱歉，出了一点问题，请稍后再试～' })
  }
  loading.value = false
  await nextTick(); scrollBottom()
}

function switchMode(m) { mode.value = m; messages.value.push({ role: 'ai', type: 'text', content: HINTS[m] }); nextTick(() => scrollBottom()) }
function scrollBottom() {
  const el = document.querySelector('.chat-area')
  if (el) el.scrollTop = el.scrollHeight
}
</script>

<template>
  <div class="chat-page">
    <div class="mode-bar">
      <button :class="['mode-btn', { active: mode === 'recommend' }]" @click="switchMode('recommend')">🛒 选购推荐</button>
      <button :class="['mode-btn', { active: mode === 'qa' }]" @click="switchMode('qa')">💬 知识问答</button>
    </div>

    <div class="chat-area">
      <div v-for="(msg, i) in messages" :key="i">
        <!-- 用户 -->
        <div v-if="msg.role === 'user'" class="msg-row right">
          <div class="bubble user">{{ msg.content }}</div>
        </div>
        <!-- AI 文字 -->
        <div v-else-if="msg.type === 'text'" class="msg-row left">
          <div class="avatar">🍊</div>
          <div class="bubble ai" style="white-space: pre-wrap;">{{ msg.content }}</div>
        </div>
        <!-- AI 推荐 -->
        <div v-else-if="msg.type === 'recommend'" class="msg-row left">
          <div class="avatar">🍊</div>
          <div class="bubble ai rec-bubble">
            <div style="margin-bottom:8px;font-weight:600;">{{ msg.content }}</div>
            <PomeloCard v-for="item in msg.items" :key="item.id" :item="item" />
          </div>
        </div>
        <!-- 加载 -->
        <div v-else-if="msg.type === 'loading'" class="msg-row left">
          <div class="avatar">🍊</div>
          <div class="bubble ai loading-bubble">
            <span class="dot">●</span><span class="dot">●</span><span class="dot">●</span>
            <span class="loading-tip">AI 正在思考...</span>
          </div>
        </div>
      </div>
    </div>

    <div class="input-bar">
      <input class="input" v-model="inputText" placeholder="输入你的需求或问题..."
             @keyup.enter="send" :disabled="loading" />
      <button class="btn btn-gold" @click="send" :disabled="loading">发送</button>
    </div>
  </div>
</template>

<style scoped>
.chat-page { display: flex; flex-direction: column; height: calc(100vh - 136px); }

.mode-bar { display: flex; gap: 10px; margin-bottom: 16px; background: var(--bg-card); border-radius: 24px; padding: 4px; border: 1px solid var(--border-light); }
.mode-btn { flex: 1; padding: 10px; border-radius: 22px; border: none; background: transparent; cursor: pointer; font-size: 13px; font-weight: 600; color: var(--text-secondary); transition: all .2s; }
.mode-btn.active { background: var(--primary); color: #fff; box-shadow: var(--shadow-button); }

.chat-area { flex: 1; overflow-y: auto; padding: 4px 0; scroll-behavior: smooth; }
.msg-row { display: flex; margin-bottom: 20px; gap: 10px; animation: fadeUp .35s ease both; }
.msg-row.right { justify-content: flex-end; }

.avatar { width: 38px; height: 38px; border-radius: 50%; background: var(--gold-light); display: flex; align-items: center; justify-content: center; font-size: 18px; flex-shrink: 0; }

.bubble { max-width: 72%; padding: 14px 18px; border-radius: 20px; font-size: .9rem; line-height: 1.7; word-break: break-word; }
.bubble.user { background: linear-gradient(135deg, var(--primary), #e8746e); color: #fff; border-bottom-right-radius: 6px; }
.bubble.ai { background: var(--bg-card); border: 1px solid var(--border-light); border-bottom-left-radius: 6px; box-shadow: var(--shadow-card); }
.rec-bubble { max-width: 90%; padding: 18px; }

.loading-bubble { display: flex; align-items: center; gap: 8px; padding: 14px 22px; }
.dot { width: 8px; height: 8px; border-radius: 50%; background: var(--primary); animation: dotBounce 1.4s infinite ease-in-out both; display: inline-block; }
.dot:nth-child(1) { animation-delay: 0s; }
.dot:nth-child(2) { animation-delay: .2s; }
.dot:nth-child(3) { animation-delay: .4s; }
.loading-tip { font-size: .8rem; color: var(--text-placeholder); margin-left: 4px; }

.input-bar { display: flex; gap: 12px; padding: 12px 0 8px; background: var(--bg-paper); }
.input-bar :deep(input) {
  flex: 1; padding: 14px 20px; border: 1.5px solid var(--border); border-radius: 26px;
  font-size: .9rem; outline: none; background: var(--bg-card); color: var(--text-primary);
  transition: border-color .2s;
}
.input-bar :deep(input):focus { border-color: var(--primary); }
.input-bar :deep(input)::placeholder { color: var(--text-placeholder); }
</style>
