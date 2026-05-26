<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api } from '../api/request'

const route = useRoute()
const router = useRouter()
const entity = ref(null)
const loading = ref(true)

onMounted(async () => {
  try { entity.value = await api.getKnowledgeById(route.params.id) }
  catch { entity.value = null }
  loading.value = false
})
function askAbout() {
  if (entity.value) {
    localStorage.setItem('quick_query', '帮我介绍一下' + (entity.value.pomeloName || ''))
    router.push('/chat')
  }
}
</script>

<template>
  <div v-if="loading" class="loading-text">加载中...</div>
  <div v-else-if="!entity" class="empty">金柚信息不存在</div>
  <div v-else class="detail">
    <div class="card">
      <h1 class="detail-name">{{ entity.pomeloName }}</h1>
      <div class="meta-grid">
        <div><span class="ml">产地</span><span>{{ entity.origin || '-' }}</span></div>
        <div><span class="ml">品类</span><span>{{ entity.category || '-' }}</span></div>
        <div><span class="ml">规格</span><span>{{ entity.specification || '-' }}</span></div>
        <div><span class="ml">价格</span><span class="price">{{ entity.priceRange || '-' }}</span></div>
        <div><span class="ml">重量</span><span>{{ entity.weightRange || '-' }}</span></div>
        <div><span class="ml">季节</span><span>{{ entity.seasonInfo || '-' }}</span></div>
      </div>
    </div>
    <div class="card" v-if="entity.tasteDescription"><h3>口感风味</h3><p>{{ entity.tasteDescription }}</p></div>
    <div class="card" v-if="entity.cultivationProcess"><h3>种植工艺</h3><p>{{ entity.cultivationProcess }}</p></div>
    <div class="card" v-if="entity.hakkaCultureRelation"><h3>🏮 客家文化</h3><p>{{ entity.hakkaCultureRelation }}</p></div>
    <div class="card" v-if="entity.ediblePairing"><h3>食用搭配</h3><p>{{ entity.ediblePairing }}</p></div>
    <div class="card" v-if="entity.preservationMethod"><h3>保鲜储藏</h3><p>{{ entity.preservationMethod }}</p></div>
    <button class="btn btn-gold" style="width:100%;margin-top:8px;" @click="askAbout">向AI了解更多</button>
  </div>
</template>

<style scoped>
.detail-name { font-size: 22px; font-weight: 800; margin-bottom: 16px; }
.meta-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.meta-grid div { padding: 8px 0; border-bottom: 1px solid #f5f5f5; font-size: 14px; }
.ml { color: #999; font-size: 12px; display: block; margin-bottom: 4px; }
.price { color: #e8684a; font-weight: 600; }
.card h3 { font-size: 15px; font-weight: 600; margin-bottom: 10px; color: #5a4636; }
.card p { font-size: 14px; line-height: 1.8; }
</style>
