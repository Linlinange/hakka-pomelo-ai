<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '../stores/user'
import { api } from '../api/request'

const router = useRouter()
const user = useUserStore()
const history = ref([])

onMounted(async () => {
  if (!user.isLogin) { router.push('/login'); return }
  try { history.value = (await api.getHistory()) || [] } catch {}
})

function goChat(q) { localStorage.setItem('quick_query', q); router.push('/chat') }
function doLogout() { user.logout(); router.push('/') }
</script>

<template>
  <div class="profile" v-if="user.isLogin">
    <div class="card profile-card">
      <div class="avatar-big">🍊</div>
      <div class="info">
        <div class="nickname">{{ user.nickname }}</div>
        <div class="uid">ID: {{ user.userId }}</div>
      </div>
    </div>

    <div class="card">
      <div style="display:flex;justify-content:space-between;align-items:center;">
        <h3 style="margin-bottom:12px;">近期提问</h3>
        <router-link to="/admin" style="font-size:13px;color:var(--gold);">⚙️ 管理后台</router-link>
      </div>
      <div v-if="history.length === 0" class="empty" style="padding:20px;">暂无提问记录</div>
      <div v-for="h in history.slice(0, 10)" :key="h.id" class="history-item" @click="goChat(h.originalInput)">
        <div class="h-query">{{ h.originalInput }}</div>
        <div class="h-time">{{ h.createTime }}</div>
      </div>
    </div>

    <button class="btn btn-red" style="width:100%;" @click="doLogout">退出登录</button>
  </div>
</template>

<style scoped>
.profile-card { display: flex; align-items: center; gap: 20px; }
.avatar-big { width: 72px; height: 72px; border-radius: 50%; background: var(--gold-light); display: flex; align-items: center; justify-content: center; font-size: 36px; }
.nickname { font-size: 20px; font-weight: 700; }
.uid { font-size: 13px; color: var(--text-placeholder); margin-top: 4px; }
.history-item { padding: 14px 0; border-bottom: 1px solid var(--border-light); cursor: pointer; }
.history-item:hover { color: var(--gold); }
.h-query { font-size: 14px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.h-time { font-size: 12px; color: var(--text-placeholder); margin-top: 4px; }
</style>
