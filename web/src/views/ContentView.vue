<script setup>
import { ref } from 'vue'
import { api } from '../api/request'

const scene = ref('social')
const pomeloName = ref('客家金柚')
const style = ref('温暖亲切')
const prompt = ref('')
const result = ref(null)
const loading = ref(false)
const copied = ref(false)

const styles = ['温暖亲切', '专业正式', '文艺清新', '活泼有趣', '高端大气']

async function generate() {
  if (loading.value) return
  loading.value = true; result.value = null; copied.value = false
  try {
    result.value = await api.generateContent({
      scene: scene.value, pomeloName: pomeloName.value,
      style: style.value, prompt: prompt.value,
    })
  } catch { alert('生成失败，请确认后端已启动') }
  loading.value = false
}

async function copy() {
  if (!result.value) return
  await navigator.clipboard.writeText(result.value.content)
  copied.value = true
  setTimeout(() => { copied.value = false }, 2000)
}
</script>

<template>
  <div class="content-page">
    <div class="page-header">
      <h1 class="page-title">✍️ 金柚文案生成</h1>
      <p class="page-subtitle">AI 为你创作电商详情页、朋友圈推广文案</p>
    </div>

    <!-- 场景选择 -->
    <div class="card" style="margin-bottom:16px;">
      <label class="form-label">使用场景</label>
      <div class="scene-tabs">
        <button :class="['scene-tab', { active: scene === 'social' }]" @click="scene = 'social'">
          <span class="scene-icon">📱</span>
          <div>
            <div class="scene-name">朋友圈推文</div>
            <div class="scene-desc">适合微信分享</div>
          </div>
        </button>
        <button :class="['scene-tab', { active: scene === 'ecommerce' }]" @click="scene = 'ecommerce'">
          <span class="scene-icon">🛒</span>
          <div>
            <div class="scene-name">电商详情页</div>
            <div class="scene-desc">适合商品展示</div>
          </div>
        </button>
      </div>
    </div>

    <!-- 参数配置 -->
    <div class="card" style="margin-bottom:16px;">
      <div class="form-group">
        <label class="form-label">金柚品名</label>
        <input class="input" v-model="pomeloName" placeholder="如：梅县松口沙田柚" />
      </div>
      <div class="form-group">
        <label class="form-label">文案风格</label>
        <div class="style-chips">
          <button v-for="s in styles" :key="s"
            :class="['style-chip', { active: style === s }]"
            @click="style = s">{{ s }}</button>
        </div>
      </div>
      <div class="form-group">
        <label class="form-label">自定义要求（可选）</label>
        <textarea class="textarea" v-model="prompt"
          placeholder="如：突出中秋送礼、客家文化元素、控制在200字以内"
          rows="3" />
      </div>
      <button class="btn btn-gold btn-lg" style="width:100%;" @click="generate" :disabled="loading">
        <span v-if="loading" class="loading-spinner"></span>
        {{ loading ? 'AI 正在创作...' : '✨ 生成文案' }}
      </button>
    </div>

    <!-- 结果展示 -->
    <div class="card result-card" v-if="result">
      <div class="result-header">
        <span class="tag" :class="result.scene === 'ecommerce' ? 'tag-gold' : 'tag-red'">
          {{ result.scene === 'ecommerce' ? '电商文案' : '朋友圈推文' }}
        </span>
        <span class="result-meta">{{ result.pomelo_name }} · {{ result.created_at }}</span>
      </div>
      <div class="result-content">{{ result.content }}</div>
      <div class="result-actions">
        <button class="btn btn-outline btn-sm" @click="copy">
          {{ copied ? '✅ 已复制' : '📋 复制文案' }}
        </button>
        <button class="btn btn-ghost btn-sm" @click="generate">🔄 重新生成</button>
      </div>
    </div>

    <div style="height:40px"></div>
  </div>
</template>

<style scoped>
.page-header { margin-bottom: 24px; }

/* === 场景选择 === */
.scene-tabs { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
.scene-tab {
  display: flex; align-items: center; gap: 14px;
  padding: 16px; border-radius: var(--radius-md);
  border: 2px solid var(--border-light); background: var(--bg-card);
  cursor: pointer; transition: all .2s; text-align: left;
}
.scene-tab:hover { border-color: var(--gold); }
.scene-tab.active { border-color: var(--primary); background: var(--primary-light); }
.scene-icon { font-size: 28px; }
.scene-name { font-size: 15px; font-weight: 700; color: var(--text-primary); }
.scene-desc { font-size: 12px; color: var(--text-placeholder); margin-top: 2px; }

/* === 表单 === */
.form-label { display: block; font-size: 13px; font-weight: 600; color: var(--text-secondary); margin-bottom: 8px; }
.form-group { margin-bottom: 18px; }

.style-chips { display: flex; flex-wrap: wrap; gap: 8px; }
.style-chip {
  padding: 8px 16px; border-radius: var(--radius-full);
  border: 1.5px solid var(--border); background: var(--bg-card);
  cursor: pointer; font-size: 13px; font-weight: 500;
  color: var(--text-secondary); transition: all .2s;
}
.style-chip:hover { border-color: var(--gold); color: var(--text-primary); }
.style-chip.active { background: var(--gold); color: #fff; border-color: var(--gold); }

/* === 加载动画 === */
.loading-spinner {
  width: 18px; height: 18px; border: 2px solid rgba(255,255,255,.3);
  border-top-color: #fff; border-radius: 50%; animation: spin .6s linear infinite;
  display: inline-block;
}

/* === 结果卡 === */
.result-card { margin-top: 16px; }
.result-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.result-meta { font-size: 12px; color: var(--text-placeholder); }
.result-content {
  font-size: 15px; line-height: 1.9; white-space: pre-wrap;
  background: var(--bg-warm); padding: 20px; border-radius: var(--radius-sm);
  color: var(--text-primary); font-family: var(--font-body);
}
.result-actions { display: flex; gap: 8px; margin-top: 16px; }

@keyframes spin { to { transform: rotate(360deg); } }
</style>
