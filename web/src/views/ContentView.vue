<script setup>
import { ref } from 'vue'
import { api } from '../api/request'

const scene = ref('social')
const pomeloName = ref('客家金柚')
const prompt = ref('')
const result = ref(null)
const loading = ref(false)

async function generate() {
  loading.value = true; result.value = null
  try { result.value = await api.generateContent({ scene: scene.value, pomeloName: pomeloName.value, prompt: prompt.value }) }
  catch { alert('生成失败，请重试') }
  loading.value = false
}
async function copy() {
  if (!result.value) return
  await navigator.clipboard.writeText(result.value.content)
  alert('已复制到剪贴板')
}
</script>

<template>
  <div class="content-page">
    <h1 class="page-title">✍️ 金柚文案生成</h1>
    <div class="card">
      <div class="tabs">
        <button :class="['tab', { active: scene === 'social' }]" @click="scene = 'social'">📱 朋友圈推文</button>
        <button :class="['tab', { active: scene === 'ecommerce' }]" @click="scene = 'ecommerce'">🛒 电商详情页</button>
      </div>
      <div class="form-item"><label>金柚品名</label><input class="input" v-model="pomeloName" placeholder="如：梅县松口沙田柚" /></div>
      <div class="form-item"><label>自定义要求（可选）</label><textarea class="textarea" v-model="prompt" placeholder="如：突出中秋送礼、客家文化元素" /></div>
      <button class="btn btn-gold" @click="generate" :disabled="loading" style="width:100%;">
        {{ loading ? 'AI 正在创作...' : '✨ 生成文案' }}
      </button>
    </div>
    <div class="card" v-if="result">
      <div class="result-head">
        <span class="tag">{{ result.scene === 'ecommerce' ? '电商文案' : '朋友圈推文' }}</span>
        <span class="result-time">{{ result.createdAt }}</span>
      </div>
      <pre class="result-content">{{ result.content }}</pre>
      <button class="btn btn-outline" @click="copy" style="margin-top:12px;">📋 复制文案</button>
    </div>
  </div>
</template>

<style scoped>
.tabs { display: flex; gap: 12px; margin-bottom: 20px; }
.tab { flex: 1; padding: 10px; border-radius: 14px; border: 1px solid #ece4d0; background: #fff; cursor: pointer; font-size: 14px; }
.tab.active { background: #d4a843; color: #fff; border-color: #d4a843; }
.form-item { margin-bottom: 16px; }
.form-item label { display: block; margin-bottom: 8px; font-size: 13px; color: #666; }
.result-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px; }
.result-time { font-size: 12px; color: #bbb; }
.result-content { font-size: 14px; line-height: 1.8; white-space: pre-wrap; background: #faf8f0; padding: 16px; border-radius: 12px; }
</style>
