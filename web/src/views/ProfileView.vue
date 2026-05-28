<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '../stores/user'
import { api } from '../api/request'

const router = useRouter()
const user = useUserStore()
const history = ref([])
const sessions = ref([])

onMounted(async () => {
  if (!user.isLogin) { router.push('/login'); return }
  try { history.value = (await api.getHistory()) || [] } catch {}
  try { sessions.value = await api.getSessions(user.userId, 10) } catch {}
})

function goChat(q) { localStorage.setItem('quick_query', q); router.push('/chat') }
function doLogout() { user.logout(); router.push('/') }
</script>

<template>
  <div class="profile" v-if="user.isLogin">
    <!-- 个人信息卡 -->
    <div class="card profile-card">
      <div class="avatar-big">🍐</div>
      <div class="profile-info">
        <div class="nickname">{{ user.nickname || '金柚爱好者' }}</div>
        <div class="uid">ID: {{ user.userId }}</div>
      </div>
      <router-link to="/admin" class="admin-link" v-if="user.userId === 1">⚙️ 管理后台</router-link>
    </div>

    <!-- 近期提问 -->
    <div class="card" style="margin-top:16px;">
      <h3 class="section-title">📝 近期提问</h3>
      <div v-if="history.length === 0" class="empty">暂无提问记录</div>
      <div v-for="h in history.slice(0, 10)" :key="h.id" class="history-item" @click="goChat(h.originalInput)">
        <div class="h-query">{{ h.originalInput }}</div>
        <div class="h-time">{{ h.createTime }}</div>
      </div>
    </div>

    <!-- 会话列表 -->
    <div class="card" style="margin-top:16px;" v-if="sessions.length > 0">
      <h3 class="section-title">💬 历史会话</h3>
      <div v-for="s in sessions.slice(0, 8)" :key="s.session_id" class="history-item">
        <div class="h-query" style="font-family:var(--font-mono);">{{ s.session_id?.slice(0, 16) }}...</div>
        <div class="h-time">{{ s.msg_count }} 条消息</div>
      </div>
    </div>

    <button class="btn btn-red" style="width:100%;margin-top:24px;" @click="doLogout">退出登录</button>
    <div style="height:40px"></div>
  </div>
</template>

<style scoped>
.profile-card {
  display: flex; align-items: center; gap: 20px;
  position: relative;
}
.avatar-big {
  width: 68px; height: 68px; border-radius: 50%;
  background: linear-gradient(135deg, var(--gold-light), #fef7ee);
  display: flex; align-items: center; justify-content: center;
  font-size: 32px; flex-shrink: 0;
  box-shadow: var(--shadow-sm);
}
.profile-info { flex: 1; }
.nickname { font-size: 20px; font-weight: 700; color: var(--text-heading); }
.uid { font-size: 13px; color: var(--text-placeholder); margin-top: 4px; }
.admin-link {
  position: absolute; top: 16px; right: 16px;
  font-size: 13px; color: var(--gold); font-weight: 600;
  text-decoration: none; padding: 4px 12px; border-radius: var(--radius-full);
  border: 1px solid var(--gold); transition: all .2s;
}
.admin-link:hover { background: var(--gold-light); }

.section-title {
  font-family: var(--font-heading); font-size: 1rem; font-weight: 700;
  color: var(--text-heading); margin-bottom: 14px;
}

.history-item {
  padding: 14px 0; border-bottom: 1px solid var(--border-light);
  cursor: pointer; transition: color .15s;
}
.history-item:last-child { border-bottom: none; }
.history-item:hover { color: var(--primary); }
.h-query {
  font-size: 14px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}
.h-time { font-size: 12px; color: var(--text-placeholder); margin-top: 4px; }

.empty { text-align: center; padding: 28px; color: var(--text-placeholder); font-size: 13px; }
</style>
