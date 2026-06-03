<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api } from '../api/request'

const route = useRoute()

// Handle both camelCase and snake_case API responses
function field(key) {
  if (!entity.value) return ''
  return entity.value[key] || entity.value[toSnake(key)] || ''
}
function toSnake(s) { return s.replace(/([A-Z])/g, '_').toLowerCase() }
const router = useRouter()
const entity = ref(null)
const loading = ref(true)

onMounted(async () => {
  try { entity.value = await api.getKnowledgeById(route.params.id) }
  catch { entity.value = null }
  loading.value = false
})

const productType = () => field('productType') || 'pomelo'
const isPomelo = () => productType() === 'pomelo'

function askAbout() {
  if (entity.value) {
    localStorage.setItem('quick_query', '帮我介绍一下' + (entity.value.pomeloName || field('pomeloName')))
    localStorage.setItem('quick_query_mode', 'qa')
    router.push('/chat')
  }
}

function goChat() {
  localStorage.setItem('quick_query', '推荐类似' + (entity.value?.pomeloName || '产品'))
  router.push('/chat')
}
</script>

<template>
  <div v-if="loading" class="loading-text">
    <div class="skeleton" style="height:200px;margin-bottom:16px;"></div>
    <div class="skeleton" style="height:120px;margin-bottom:16px;"></div>
    <div class="skeleton" style="height:120px;"></div>
  </div>

  <div v-else-if="!entity" class="empty">
    <span class="empty-icon">🍐</span>
    <p>产品信息不存在</p>
  </div>

  <div v-else class="detail anim-fade-up">
    <!-- 头部信息卡 -->
    <div class="hero-card card">
      <div class="hero-top">
        <span class="tag tag-red" v-if="field('category')">{{ field('category') }}</span>
        <span class="tag tag-gold" v-if="field('seasonInfo')">{{ field('seasonInfo') }}</span>
      </div>
      <h1 class="hero-name">{{ field('pomeloName') }}</h1>
      <p class="hero-origin" v-if="field('origin')">📍 {{ field('origin') }}</p>

      <!-- 属性网格 -->
      <div class="attr-grid">
        <div class="attr-item" v-if="field('priceRange')">
          <span class="attr-label">参考价格</span>
          <span class="attr-value price">{{ field('priceRange') }}</span>
        </div>
        <div class="attr-item" v-if="field('specification')">
          <span class="attr-label">规格</span>
          <span class="attr-value">{{ field('specification') }}</span>
        </div>
        <div class="attr-item" v-if="field('weightRange')">
          <span class="attr-label">单果重量</span>
          <span class="attr-value">{{ field('weightRange') }}</span>
        </div>
        <div class="attr-item">
          <span class="attr-label">送礼标签</span>
          <span class="attr-value" v-if="field('giftSceneTags')">{{ field('giftSceneTags') }}</span>
          <span class="attr-value muted" v-else>暂无</span>
        </div>
      </div>

      <!-- 评分概览 -->
      <div class="scores-row" v-if="field('scoreRequirementMatch') || field('scoreSceneFit') || field('scoreHakkaFeature')">
        <div class="mini-score">
          <div class="mini-score-ring" :style="{ '--pct': (field('scoreRequirementMatch') || 0) * 10 + '%' }">
            <span>{{ (field('scoreRequirementMatch') || 0).toFixed(1) }}</span>
          </div>
          <span class="mini-label">需求匹配</span>
        </div>
        <div class="mini-score">
          <div class="mini-score-ring scene" :style="{ '--pct': (field('scoreSceneFit') || 0) * 10 + '%' }">
            <span>{{ (field('scoreSceneFit') || 0).toFixed(1) }}</span>
          </div>
          <span class="mini-label">场景适配</span>
        </div>
        <div class="mini-score">
          <div class="mini-score-ring hakka" :style="{ '--pct': (field('scoreHakkaFeature') || 0) * 10 + '%' }">
            <span>{{ (field('scoreHakkaFeature') || 0).toFixed(1) }}</span>
          </div>
          <span class="mini-label">{{ isPomelo() ? '客家特色' : '产品特色' }}</span>
        </div>
        <!-- 非pomelo显示 product_feature -->
        <div class="mini-score" v-if="!isPomelo() && field('scoreProductFeature')">
          <div class="mini-score-ring" :style="{ '--pct': (field('scoreProductFeature') || 0) * 10 + '%' }">
            <span>{{ (field('scoreProductFeature') || 0).toFixed(1) }}</span>
          </div>
          <span class="mini-label">综合特色</span>
        </div>
      </div>

      <!-- 操作按钮 -->
      <div class="hero-actions">
        <button class="btn btn-primary" @click="goChat">🤖 推荐类似产品</button>
        <button class="btn btn-outline" @click="askAbout">📖 向AI了解更多</button>
      </div>
    </div>

    <!-- 详情分段 -->
    <div class="card section-card" v-if="field('tasteDescription')">
      <h3>👅 口感风味</h3>
      <p>{{ field('tasteDescription') }}</p>
    </div>

    <div class="card section-card" v-if="field('cultivationProcess')">
      <h3>🌱 种植工艺</h3>
      <p>{{ field('cultivationProcess') }}</p>
    </div>

    <div class="card section-card" v-if="field('productDescription') && !isPomelo()">
      <h3>📖 产品特色</h3>
      <p>{{ field('productDescription') }}</p>
    </div>

    <div class="card section-card" v-if="field('hakkaCultureRelation') && isPomelo()">
      <h3>🏯 客家文化</h3>
      <p>{{ field('hakkaCultureRelation') }}</p>
    </div>

    <div class="card section-card" v-if="field('ediblePairing')">
      <h3>🍽️ 食用搭配</h3>
      <p>{{ field('ediblePairing') }}</p>
    </div>

    <div class="card section-card" v-if="field('preservationMethod')">
      <h3>📦 保鲜储藏</h3>
      <p>{{ field('preservationMethod') }}</p>
    </div>

    <div class="card section-card" v-if="field('nutritionalValue')">
      <h3>💪 营养价值</h3>
      <p>{{ field('nutritionalValue') }}</p>
    </div>

    <div class="card section-card" v-if="field('identificationTips')">
      <h3>🔍 辨别技巧</h3>
      <p>{{ field('identificationTips') }}</p>
    </div>

    <div style="height:40px"></div>
  </div>
</template>

<style scoped>
.detail { padding-bottom: 20px; }

/* === 头部 === */
.hero-card { padding: 24px; }
.hero-top { display: flex; gap: 8px; margin-bottom: 16px; }
.hero-name {
  font-family: var(--font-heading); font-size: 1.6rem; font-weight: 900;
  color: var(--text-heading); line-height: 1.3; margin-bottom: 8px;
}
.hero-origin { font-size: .9rem; color: var(--text-secondary); margin-bottom: 20px; }

/* 属性网格 */
.attr-grid {
  display: grid; grid-template-columns: 1fr 1fr; gap: 14px;
  padding: 16px; background: var(--bg-warm); border-radius: var(--radius-sm);
  margin-bottom: 20px;
}
.attr-item { display: flex; flex-direction: column; gap: 2px; }
.attr-label { font-size: 11px; color: var(--text-placeholder); text-transform: uppercase; letter-spacing: .04em; }
.attr-value { font-size: 14px; font-weight: 600; color: var(--text-primary); }
.attr-value.price { color: var(--primary); font-size: 16px; }
.attr-value.muted { color: var(--text-placeholder); font-weight: 400; }

/* 评分圆环 */
.scores-row { display: flex; justify-content: space-around; margin-bottom: 20px; padding: 4px 0; }
.mini-score { display: flex; flex-direction: column; align-items: center; gap: 6px; }
.mini-score-ring {
  width: 56px; height: 56px; border-radius: 50%;
  background: conic-gradient(var(--primary) 0% var(--pct, 0%), var(--border-light) var(--pct, 0%) 100%);
  display: flex; align-items: center; justify-content: center;
  position: relative;
}
.mini-score-ring::after {
  content: ''; width: 42px; height: 42px; border-radius: 50%;
  background: var(--bg-card); position: absolute;
}
.mini-score-ring span {
  z-index: 1; font-size: 14px; font-weight: 800; color: var(--primary);
}
.mini-score-ring.scene { background: conic-gradient(var(--gold) 0% var(--pct, 0%), var(--border-light) var(--pct, 0%) 100%); }
.mini-score-ring.scene span { color: var(--gold-deep); }
.mini-score-ring.hakka { background: conic-gradient(#788c5d 0% var(--pct, 0%), var(--border-light) var(--pct, 0%) 100%); }
.mini-score-ring.hakka span { color: #5a6b42; }
.mini-label { font-size: 11px; color: var(--text-placeholder); }

/* 操作按钮 */
.hero-actions { display: flex; gap: 10px; }
.hero-actions .btn { flex: 1; }

/* 详情段 */
.section-card { margin-top: 14px; }
.section-card h3 {
  font-family: var(--font-heading); font-size: 1rem; font-weight: 700;
  color: var(--text-heading); margin-bottom: 12px;
}
.section-card p { font-size: .9rem; line-height: 1.85; color: var(--text-primary); }
</style>
