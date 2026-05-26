<script setup>
import PomeloCard from './PomeloCard.vue'
defineProps({ items: { type: Array, default: () => [] } })
</script>

<template>
  <div class="grid">
    <PomeloCard v-for="item in items" :key="item.id" :item="item" />
    <div v-if="items.length === 0" class="empty">暂无数据</div>
  </div>
</template>

<style scoped>
.grid { display: flex; flex-direction: column; }
</style>
