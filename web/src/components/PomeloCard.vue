<script setup>
import { computed, ref } from 'vue'

const props = defineProps({
  item: { type: Object, required: true },
  showDetail: { type: Boolean, default: true },
  showScoring: { type: Boolean, default: false },
})

const expanded = ref(false)

const productType = computed(() => props.item.productType || props.item.product_type || 'pomelo')
const name = computed(() => props.item.pomeloName || props.item.pomelo_name || '')
const origin = computed(() => props.item.origin || '')
const price = computed(() => props.item.priceRange || props.item.price_range || '')
const taste = computed(() => props.item.tasteDescription || props.item.taste_description || '')
const culture = computed(() => props.item.hakkaCultureRelation || props.item.hakka_culture_relation || '')
const imageUrl = computed(() => props.item.imageUrl || props.item.image_url || '')
const score = computed(() => Math.round(Number(props.item.finalScore || props.item.final_score) || 0))
const stars = computed(() => Math.round(score.value / 20))
const tags = computed(() => {
  const s = [props.item.giftSceneTags || props.item.gift_scene_tags, props.item.tags].filter(Boolean).join(',')
  return s.split(/[,，]/).map(t => t.trim()).filter(Boolean).slice(0, 3)
})

// 打分明细
const scorePrice = computed(() => Number(props.item.scorePriceMatch || props.item.score_price_match || 0).toFixed(1))
const scoreScene = computed(() => Number(props.item.scoreSceneFit || props.item.score_scene_fit || 0).toFixed(1))
// 第三维度：pomelo→score_hakka_feature，其他→score_product_feature
const scoreThird = computed(() => {
  if (productType.value === 'pomelo') {
    return Number(props.item.scoreHakkaFeature || props.item.score_hakka_feature || 0).toFixed(1)
  }
  return Number(props.item.scoreProductFeature || props.item.score_product_feature || 0).toFixed(1)
})
const thirdLabel = computed(() => productType.value === 'pomelo' ? '客家特色' : '产品特色')
const ruleTotal = computed(() => Number(props.item.ruleTotal || props.item.rule_total || 0).toFixed(1))
const llmScore = computed(() => Number(props.item.llmScore || props.item.llm_score || 0).toFixed(0))

function goDetail() {
  if (props.item.id) {
    window..push('/detail/' + props.item.id)
  }
}
</script>

<template>
  <div class="pomelo-card" @click="goDetail">
    <!-- 左侧媒体区 -->
    <div class="card-media">
      <img v-if="imageUrl" :src="imageUrl" :alt="name" class="card-img" />
      <div v-else class="card-img-placeholder">
        <span class="card-emoji">{{ stars >= 4 ? '🍐' : '🍊' }}</span>
      </div>
      <!-- 评分角标 -->
      <div class="score-badge" v-if="score">
        <span class="score-num">{{ score }}</span>
        <span class="score-label">分</span>
      </div>
      <!-- 产地印 -->
      <div class="card-seal" v-if="origin">
        {{ origin?.slice(0, 4) }}产
      </div>
    </div>

    <!-- 右侧信息 -->
    <div class="card-body">
      <h3 class="card-title">{{ name }}</h3>
      <p class="card-origin" v-if="origin">{{ origin }}</p>

      <!-- 口味 -->
      <p class="card-taste" v-if="taste">{{ taste }}</p>

      <!-- 标签 -->
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
          <span class="star-text" v-if="score">{{ score }}分</span>
        </span>
      </div>

      <!-- 推荐理由 -->
      <div class="card-reason" v-if="item.reason">
        <span class="reason-mark">"</span>
        <span>{{ item.reason }}</span>
        <span class="reason-mark">"</span>
      </div>

      <!-- 打分明细（可展开） -->
      <div v-if="showScoring && (scorePrice > 0 || scoreScene > 0 || scoreThird > 0)" class="scoring-section">
        <button class="scoring-toggle" @click.stop="expanded = !expanded">
          {{ expanded ? '收起' : '查看' }}打分详情
          <span :class="{ rotated: expanded }">▾</span>
        </button>
        <transition name="expand">
          <div v-if="expanded" class="scoring-detail">
            <div class="score-row">
              <span class="score-label-text">价格匹配</span>
              <div class="score-bar-bg"><div class="score-bar-fill price" :style="{ width: (scorePrice * 10) + '%' }"></div></div>
              <span class="score-val">{{ scorePrice }}</span>
            </div>
            <div class="score-row">
              <span class="score-label-text">场景适配</span>
              <div class="score-bar-bg"><div class="score-bar-fill scene" :style="{ width: (scoreScene * 10) + '%' }"></div></div>
              <span class="score-val">{{ scoreScene }}</span>
            </div>
            <div class="score-row">
              <span class="score-label-text">{{ thirdLabel }}</span>
              <div class="score-bar-bg"><div class="score-bar-fill hakka" :style="{ width: (scoreThird * 10) + '%' }"></div></div>
              <span class="score-val">{{ scoreThird }}</span>
            </div>
            <div class="score-row total">
              <span class="score-label-text">规则总分</span>
              <span class="score-val bold">{{ ruleTotal }}</span>
            </div>
            <div class="score-row llm" v-if="Number(llmScore) > 0">
              <span class="score-label-text">AI 语义评分</span>
              <span class="score-val bold">{{ llmScore }}</span>
            </div>
          </div>
        </transition>
      </div>
    </div>
  </div>
</template>

<style scoped>
.pomelo-card {
  background: var(--bg-card); border-radius: var(--radius-lg);
  overflow: hidden; cursor: pointer;
  box-shadow: var(--shadow-card); border: 1px solid var(--border-light);
  transition: all .3s var(--ease-out);
  display: flex; gap: 0;
}
.pomelo-card:hover {
  box-shadow: var(--shadow-md); transform: translateY(-2px);
}

/* === 左侧媒体 === */
.card-media {
  width: 150px; min-height: 180px; flex-shrink: 0;
  position: relative; overflow: hidden;
  background: linear-gradient(160deg, var(--gold-light) 0%, #fef7ee 100%);
}
.card-img {
  width: 100%; height: 100%; object-fit: cover;
}
.card-img-placeholder {
  width: 100%; height: 100%; display: flex; align-items: center; justify-content: center;
}
.card-emoji { font-size: 56px; }

.score-badge {
  position: absolute; top: 10px; right: 10px;
  background: rgba(255,255,255,0.92); backdrop-filter: blur(8px);
  border-radius: var(--radius-xs); padding: 4px 10px;
  display: flex; align-items: baseline; gap: 2px;
  box-shadow: var(--shadow-sm);
}
.score-num { font-size: 20px; font-weight: 800; color: var(--primary); line-height: 1; }
.score-label { font-size: 10px; color: var(--text-placeholder); }

.card-seal {
  position: absolute; bottom: 10px; left: 10px;
  font-family: var(--font-display); font-size: 10px; font-weight: 700;
  color: var(--primary); letter-spacing: .08em;
  border: 1.5px solid rgba(217,80,74,.4);
  padding: 2px 8px; border-radius: 2px; transform: rotate(-2deg);
  background: rgba(255,255,255,0.75);
}

/* === 右侧信息 === */
.card-body {
  flex: 1; padding: 16px; display: flex; flex-direction: column; gap: 6px;
  overflow: hidden; min-width: 0;
}
.card-title {
  font-family: var(--font-heading); font-size: .95rem; font-weight: 700;
  color: var(--text-heading); line-height: 1.3;
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}
.card-origin { font-size: .78rem; color: var(--text-placeholder); }
.card-taste { font-size: .8rem; color: var(--text-secondary); line-height: 1.5; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
.card-tags { display: flex; gap: 5px; flex-wrap: wrap; }
.card-meta { display: flex; align-items: center; justify-content: space-between; margin-top: auto; }
.card-price { font-size: .95rem; font-weight: 700; color: var(--primary); }
.card-stars { font-size: 13px; display: flex; align-items: center; gap: 2px; }
.star-on  { color: var(--gold); }
.star-off { color: var(--border); }
.star-text { font-size: 11px; color: var(--text-placeholder); margin-left: 4px; }

.card-reason {
  font-size: .8rem; color: var(--text-secondary); line-height: 1.6;
  background: var(--bg-warm); border-radius: var(--radius-xs);
  padding: 10px 12px; border-left: 3px solid var(--gold);
  margin-top: 4px;
}
.reason-mark { color: var(--gold); font-family: var(--font-heading); font-size: 1.2em; }

/* === 打分明细 === */
.scoring-section { margin-top: 6px; }
.scoring-toggle {
  background: none; border: none; color: var(--text-placeholder); cursor: pointer;
  font-size: 12px; display: flex; align-items: center; gap: 4px; padding: 2px 0;
  transition: color .2s;
}
.scoring-toggle:hover { color: var(--primary); }
.scoring-toggle span { transition: transform .2s; font-size: 10px; }
.scoring-toggle span.rotated { transform: rotate(180deg); }

.scoring-detail {
  margin-top: 8px; padding: 12px; background: var(--bg-warm);
  border-radius: var(--radius-xs); display: flex; flex-direction: column; gap: 8px;
}
.score-row { display: flex; align-items: center; gap: 8px; font-size: 12px; }
.score-label-text { width: 60px; color: var(--text-secondary); flex-shrink: 0; }
.score-bar-bg { flex: 1; height: 6px; background: var(--border-light); border-radius: 3px; overflow: hidden; }
.score-bar-fill { height: 100%; border-radius: 3px; transition: width .5s var(--ease-out); }
.score-bar-fill.price { background: var(--primary); }
.score-bar-fill.scene { background: var(--gold); }
.score-bar-fill.hakka { background: #788c5d; }
.score-val { width: 32px; text-align: right; font-weight: 600; color: var(--text-primary); }
.score-val.bold { font-weight: 700; color: var(--primary); }
.score-row.total { border-top: 1px solid var(--border-light); padding-top: 6px; }
.score-row.llm { padding-top: 2px; }

/* === Expand transition === */
.expand-enter-active, .expand-leave-active { transition: all .25s var(--ease-out); overflow: hidden; }
.expand-enter-from, .expand-leave-to { opacity: 0; max-height: 0; }
.expand-enter-to, .expand-leave-from { opacity: 1; max-height: 200px; }
</style>
