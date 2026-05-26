<script setup>
import { computed } from 'vue'

const props = defineProps({
  item: { type: Object, required: true },
  showDetail: { type: Boolean, default: true },
})

const name = computed(() => props.item.pomeloName || props.item.pomelo_name || '')
const origin = computed(() => props.item.origin || '')
const price = computed(() => props.item.priceRange || props.item.price_range || '')
const score = computed(() => Math.round(Number(props.item.finalScore || props.item.final_score) || 0))
const stars = computed(() => Math.round(score.value / 20))
const tags = computed(() => {
  const s = [props.item.giftSceneTags || props.item.gift_scene_tags, props.item.tags].filter(Boolean).join(',')
  return s.split(/[,，]/).map(t => t.trim()).filter(Boolean).slice(0, 3)
})
</script>

<template>
  <div class="pomelo-card" @click="$router.push('/detail/' + item.id)">
    <!-- 头图区 -->
    <div class="card-media">
      <div class="card-img-placeholder">
        <span class="card-emoji">{{ stars >= 4 ? '🍊' : '🍋' }}</span>
      </div>
      <!-- 评分角标 -->
      <div class="score-badge" v-if="score">
        <span class="score-num">{{ score }}</span>
        <span class="score-label">分</span>
      </div>
      <!-- 印章 -->
      <div class="card-seal" v-if="item.origin">
        {{ item.origin?.slice(0,4) }}产
      </div>
    </div>

    <!-- 信息区 -->
    <div class="card-body">
      <h3 class="card-title">{{ name }}</h3>
      <p class="card-origin" v-if="origin">{{ origin }}</p>

      <!-- 标签行 -->
      <div class="card-tags" v-if="tags.length">
        <span class="tag tag-red" v-for="t in tags" :key="t">{{ t }}</span>
      </div>

      <!-- 价格 + 星级 -->
      <div class="card-meta">
        <span class="card-price" v-if="price">{{ price }}</span>
        <span class="card-stars">
          <span v-for="i in 5" :key="i" :class="i <= stars ? 'star-on' : 'star-off'">
            {{ i <= stars ? '★' : '☆' }}
          </span>
        </span>
      </div>

      <!-- 推荐理由 -->
      <div class="card-reason" v-if="item.reason">
        <span class="reason-mark">"</span>
        <span>{{ item.reason }}</span>
        <span class="reason-mark">"</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.pomelo-card {
  background: var(--bg-card); border-radius: var(--radius-lg);
  overflow: hidden; cursor: pointer;
  box-shadow: var(--shadow-card); border: 1px solid var(--border-light);
  transition: all .3s cubic-bezier(.25,.8,.25,1);
  display: flex; gap: 0;
}
.pomelo-card:hover {
  box-shadow: var(--shadow-float); transform: translateY(-3px);
}

/* 左侧媒体区 */
.card-media {
  width: 150px; min-height: 180px; flex-shrink: 0;
  position: relative; overflow: hidden;
  background: linear-gradient(160deg, var(--gold-light) 0%, #fef7ee 100%);
}
.card-img-placeholder {
  width: 100%; height: 100%; display: flex; align-items: center; justify-content: center;
}
.card-emoji { font-size: 56px; }

.score-badge {
  position: absolute; top: 10px; right: 10px;
  background: rgba(255,255,255,0.9); backdrop-filter: blur(8px);
  border-radius: var(--radius-sm); padding: 4px 10px;
  display: flex; align-items: baseline; gap: 2px;
  box-shadow: var(--shadow-card);
}
.score-num { font-size: 20px; font-weight: 800; color: var(--primary); line-height: 1; }
.score-label { font-size: 10px; color: var(--text-placeholder); }

.card-seal {
  position: absolute; bottom: 10px; left: 10px;
  font-family: var(--font-display); font-size: 10px; font-weight: 700;
  color: var(--primary); letter-spacing: .08em;
  border: 1.5px solid rgba(217,80,74,.4);
  padding: 2px 8px; border-radius: 2px; transform: rotate(-2deg);
  background: rgba(255,255,255,0.7);
}

/* 右侧信息区 */
.card-body {
  flex: 1; padding: 16px; display: flex; flex-direction: column; gap: 8px;
  overflow: hidden;
}
.card-title {
  font-family: var(--font-heading); font-size: .95rem; font-weight: 700;
  color: var(--text-heading); line-height: 1.3;
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}
.card-origin { font-size: .78rem; color: var(--text-placeholder); }
.card-tags { display: flex; gap: 6px; flex-wrap: wrap; }
.card-meta { display: flex; align-items: center; justify-content: space-between; margin-top: auto; }
.card-price { font-size: .95rem; font-weight: 700; color: var(--primary); }
.card-stars { font-size: 13px; display: flex; gap: 2px; }
.star-on  { color: var(--gold); }
.star-off { color: var(--border); }

.card-reason {
  font-size: .8rem; color: var(--text-secondary); line-height: 1.6;
  background: var(--bg-warm); border-radius: var(--radius-sm);
  padding: 10px 12px; border-left: 3px solid var(--gold);
}
.reason-mark { color: var(--gold); font-family: var(--font-heading); font-size: 1.2em; }
</style>
