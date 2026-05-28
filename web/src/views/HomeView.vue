<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../api/request'
import PomeloCard from '../components/PomeloCard.vue'

const router = useRouter()
const knowledge = ref([])
const loading = ref(true)

const hotQueries = [
  { q: '200元中秋送礼推荐什么金柚？',  label: '中秋送礼推荐',  icon: '🎵', color: '#e8684a' },
  { q: '适合老人吃的金柚有哪些？',      label: '适合老人的金柚', icon: '👘', color: '#c4a265' },
  { q: '沙田柚和蜜柚有什么区别？',      label: '沙田柚 vs 蜜柚', icon: '🍐', color: '#788c5d' },
  { q: '推荐团圆饭搭配的金柚',          label: '团圆饭搭配',    icon: '🍽️', color: '#d9504a' },
]

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
    <!-- Hero 区 -->
    <section class="hero">
      <div class="hero-glow"></div>
      <div class="hero-badge">
        <span class="seal">客家金柚</span>
        <span class="hero-badge-sub">AI 驱动 · 精准选柚</span>
      </div>
      <h1 class="hero-title">
        每一颗金柚，<br/>都值得被<span class="hero-hl">认真推荐</span>
      </h1>
      <p class="hero-desc">
        来自梅州山水间的客家金柚，AI 读懂你的需求，为你找到最合适的那一颗
      </p>
      <div class="hero-actions">
        <button class="btn btn-primary btn-lg pulse-cta" @click="goChat('')">
          🤖 开始选柚
        </button>
        <button class="btn btn-outline btn-lg" @click="router.push('/content')">
          ✍️ 生成文案
        </button>
      </div>
    </section>

    <!-- 快捷入口 -->
    <section class="section">
      <div class="section-head">
        <h2 class="section-title">🔥 大家都在问</h2>
        <span class="section-sub">点击直接提问</span>
      </div>
      <div class="hot-grid">
        <div class="hot-card anim-fade-up" v-for="(hq, i) in hotQueries"
             :key="hq.q" @click="goChat(hq.q)"
             :style="{ animationDelay: i * 0.1 + 's', '--accent': hq.color }">
          <div class="hot-icon" :style="{ background: hq.color + '15', color: hq.color }">
            {{ hq.icon }}
          </div>
          <div class="hot-info">
            <span class="hot-label">{{ hq.label }}</span>
            <span class="hot-arrow">→</span>
          </div>
        </div>
      </div>
    </section>

    <!-- 金柚精选 -->
    <section class="section">
      <div class="section-head">
        <h2 class="section-title">🍐 金柚精选</h2>
        <span class="section-sub">客家山水，自然好柚</span>
      </div>

      <div v-if="loading" class="skeleton-grid">
        <div class="skeleton" style="height:140px" v-for="i in 3" :key="i"></div>
      </div>

      <div v-else class="feed blur-stagger">
        <div class="divider-wave"></div>
        <PomeloCard v-for="item in knowledge.slice(0, 6)" :key="item.id" :item="item" />
      </div>

      <div v-if="!loading && knowledge.length === 0" class="empty-state">
        <span class="empty-icon">🍐</span>
        <p>金柚知识库加载中...</p>
        <p class="empty-hint">请确认后端服务已启动</p>
      </div>
    </section>

    <!-- 底部留白 -->
    <div style="height:40px"></div>
  </div>
</template>

<style scoped>
.home { padding-bottom: 20px; }

/* === Hero === */
.hero {
  text-align: center; padding: 48px 12px 40px; position: relative;
  overflow: hidden;
}
.hero-glow {
  position: absolute; top: -60px; left: 50%; transform: translateX(-50%);
  width: 280px; height: 280px; border-radius: 50%;
  background: radial-gradient(circle, rgba(217,80,74,0.06) 0%, rgba(196,162,101,0.04) 40%, transparent 70%);
  pointer-events: none;
}
.hero-badge {
  display: flex; flex-direction: column; align-items: center; gap: 10px;
  margin-bottom: 24px;
}
.hero-badge-sub {
  font-size: 12px; color: var(--text-placeholder); letter-spacing: .08em;
  text-transform: uppercase;
}
.hero-title {
  font-family: var(--font-heading); font-size: 2.2rem; font-weight: 900;
  color: var(--text-heading); line-height: 1.35; letter-spacing: .04em;
  margin-bottom: 16px; position: relative; z-index: 1;
}
.hero-hl {
  background: linear-gradient(180deg, transparent 58%, rgba(217,80,74,0.18) 58%);
  padding: 0 6px;
}
.hero-desc {
  font-size: .95rem; color: var(--text-secondary); margin-bottom: 32px;
  letter-spacing: .04em; max-width: 380px; margin-left: auto; margin-right: auto;
  position: relative; z-index: 1;
}
.hero-actions { display: flex; justify-content: center; gap: 14px; position: relative; z-index: 1; }

/* === Section === */
.section { margin-top: 36px; }
.section-head {
  display: flex; align-items: baseline; justify-content: space-between;
  margin-bottom: 18px;
}
.section-title {
  font-family: var(--font-heading); font-size: 1.15rem; font-weight: 700;
  color: var(--text-heading);
}
.section-sub { font-size: .82rem; color: var(--text-placeholder); }

/* === 快捷提问 === */
.hot-grid {
  display: grid; grid-template-columns: 1fr 1fr; gap: 10px;
}
.hot-card {
  background: var(--bg-card); border: 1px solid var(--border-light);
  border-radius: var(--radius-md); padding: 16px;
  cursor: pointer; transition: all .25s var(--ease-out);
  display: flex; align-items: center; gap: 12px;
}
.hot-card:hover {
  border-color: var(--accent, var(--primary));
  background: var(--primary-light);
  transform: translateY(-2px);
  box-shadow: var(--shadow-sm);
}
.hot-icon {
  width: 42px; height: 42px; border-radius: var(--radius-sm);
  display: flex; align-items: center; justify-content: center;
  font-size: 20px; flex-shrink: 0;
}
.hot-info {
  flex: 1; display: flex; align-items: center; justify-content: space-between;
}
.hot-label { font-size: .85rem; font-weight: 600; color: var(--text-primary); }
.hot-arrow { font-size: 16px; color: var(--text-placeholder); transition: transform .2s; }
.hot-card:hover .hot-arrow { transform: translateX(4px); color: var(--primary); }

/* === Skeleton === */
.skeleton-grid { display: flex; flex-direction: column; gap: 12px; }

/* === Feed === */
.feed { display: flex; flex-direction: column; gap: 14px; }

.empty-state { text-align: center; padding: 60px 0; color: var(--text-placeholder); }
.empty-icon { font-size: 48px; margin-bottom: 12px; display: block; }
.empty-hint { font-size: .8rem; margin-top: 8px; color: var(--text-placeholder); opacity: .7; }

/* === Pulse CTA === */
@keyframes pulseAttention{0%,100%{box-shadow:0 0 0 0 rgba(217,80,74,.4)}50%{box-shadow:0 0 0 14px rgba(217,80,74,0)}}
.pulse-cta{animation:pulseAttention 3s infinite}
</style>
