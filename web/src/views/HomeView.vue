<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../api/request'
import PomeloCard from '../components/PomeloCard.vue'

const router = useRouter()
const hotQueries = [
  { q: '200元中秋送礼推荐什么金柚？',   label: '中秋送礼推荐',   icon: '🎁' },
  { q: '适合老人吃的金柚有哪些？',       label: '适合老人的金柚', icon: '👴' },
  { q: '沙田柚和蜜柚有什么区别？',       label: '沙田柚 vs 蜜柚', icon: '🍊' },
  { q: '帮我推荐团圆饭搭配的金柚',       label: '团圆饭搭配',     icon: '🍽️' },
]
const knowledge = ref([])
const loading = ref(true)

onMounted(async () => {
  try { knowledge.value = (await api.getKnowledge({})) || [] } catch {}
  loading.value = false
})

function goChat(q) {
  localStorage.setItem('quick_query', q || '')
  const isQA = /怎么|如何|什么|区别|保存|营养|做法|功效|历史|哪/.test(q)
  localStorage.setItem('quick_query_mode', isQA ? 'qa' : 'recommend')
  router.push('/chat')
}
</script>

<template>
  <div class="home">
    <!-- Hero — 小红书风格 -->
    <section class="hero">
      <!-- 吉祥物：柚仔 -->
      <div class="mascot" style="margin-bottom:12px;">
        <div class="mascot-body"></div>
        <div class="mascot-shadow"></div>
      </div>
      <div class="hero-badge">
        <span class="seal">客家金柚</span>
      </div>
      <h1 class="hero-title">
        每一颗金柚，<br/>都值得被<span class="hero-hl">认真推荐</span>
      </h1>
      <p class="hero-desc">AI 读懂你的需求，从梅州山水间为你选柚</p>
      <div class="hero-actions">
        <button class="btn btn-primary" @click="goChat('')">
          🤖 开始选柚
        </button>
        <button class="btn btn-outline" @click="router.push('/content')">
          ✍️ 生成文案
        </button>
      </div>
    </section>

    <!-- 热门提问 — 横向滑动卡片 -->
    <section class="section">
      <div class="section-head">
        <h2 class="section-title">🔥 大家都在问</h2>
      </div>
      <div class="hot-scroll">
        <div class="hot-card anim-fade-up" v-for="(hq, i) in hotQueries"
             :key="hq.q" @click="goChat(hq.q)"
             :style="{ animationDelay: i * 0.1 + 's' }">
          <span class="hot-emoji">{{ hq.icon }}</span>
          <span class="hot-label">{{ hq.label }}</span>
        </div>
      </div>
    </section>

    <!-- 金柚精选 — 种草卡片流 -->
    <section class="section">
      <div class="section-head">
        <h2 class="section-title">🍊 金柚精选</h2>
        <span class="section-sub">客家山水，自然好柚</span>
      </div>

      <!-- 加载骨架屏 -->
      <div v-if="loading" class="skeleton-grid">
        <div class="skeleton card" style="height:180px" v-for="i in 3" :key="i"></div>
      </div>

      <!-- 卡片流 — 模糊交错入场 -->
      <div v-else class="feed blur-stagger">
        <!-- 檐角波浪分割线 -->
        <div class="divider-wave"></div>
        <PomeloCard v-for="item in knowledge.slice(0, 6)" :key="item.id" :item="item" />
      </div>

      <div v-if="!loading && knowledge.length === 0" class="empty-state">
        <span style="font-size:56px">🍊</span>
        <p>金柚知识库加载中...</p>
        <p class="empty-hint">请确认后端服务已启动</p>
      </div>
    </section>
  </div>
</template>

<style scoped>
.home { padding-bottom: 20px; }

/* Hero */
.hero {
  text-align: center; padding: 40px 12px 32px; position: relative;
}
.hero::after {
  content: ''; position: absolute; top: -40px; left: 50%; transform: translateX(-50%);
  width: 200px; height: 200px; border-radius: 50%;
  background: radial-gradient(circle, rgba(217,80,74,0.06) 0%, transparent 70%);
  pointer-events: none;
}
.hero-badge { margin-bottom: 20px; }
.hero-title {
  font-family: var(--font-heading); font-size: 2rem; font-weight: 900;
  color: var(--text-heading); line-height: 1.4; letter-spacing: .04em;
  margin-bottom: 12px;
}
.hero-hl {
  background: linear-gradient(180deg, transparent 60%, rgba(217,80,74,0.15) 60%);
  padding: 0 4px;
}
.hero-desc {
  font-size: .95rem; color: var(--text-secondary); margin-bottom: 28px; letter-spacing: .04em;
}
.hero-actions { display: flex; justify-content: center; gap: 14px; }

/* Section */
.section { margin-top: 32px; }
.section-head {
  display: flex; align-items: baseline; gap: 12px; margin-bottom: 16px;
}
.section-title {
  font-family: var(--font-heading); font-size: 1.15rem; font-weight: 700;
  color: var(--text-heading);
}
.section-sub { font-size: .85rem; color: var(--text-placeholder); }

/* 热门提问 — 横向卡片 */
.hot-scroll {
  display: flex; gap: 12px; overflow-x: auto; padding: 4px 0 8px;
  scroll-snap-type: x mandatory; -webkit-overflow-scrolling: touch;
}
.hot-scroll::-webkit-scrollbar { display: none; }
.hot-card {
  display: flex; align-items: center; gap: 8px; flex-shrink: 0;
  background: var(--bg-card); border: 1px solid var(--border-light);
  border-radius: 22px; padding: 12px 20px;
  cursor: pointer; transition: all .2s; scroll-snap-align: start;
}
.hot-card:hover { border-color: var(--primary); background: var(--primary-light); }
.hot-emoji { font-size: 20px; }
.hot-label { font-size: .88rem; color: var(--text-primary); white-space: nowrap; }

/* 骨架屏 */
.skeleton-grid { display: flex; flex-direction: column; gap: 14px; }

/* 卡片流 */
.feed { display: flex; flex-direction: column; gap: 14px; }

.empty-state { text-align: center; padding: 60px 0; color: var(--text-placeholder); }
.empty-hint { font-size: .8rem; margin-top: 8px; color: var(--text-placeholder); }
</style>
