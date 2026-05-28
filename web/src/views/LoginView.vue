<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '../stores/user'

const router = useRouter()
const user = useUserStore()
const loading = ref(false)

async function doLogin() {
  loading.value = true
  try {
    const code = 'web_' + Date.now()
    await user.login(code)
    router.push('/profile')
  } catch {
    alert('登录失败，请确认后端已启动')
  }
  loading.value = false
}
</script>

<template>
  <div class="login-page">
    <div class="login-card card">
      <!-- Logo -->
      <div class="login-logo">
        <div class="mascot">
          <div class="mascot-body"></div>
          <div class="mascot-shadow"></div>
        </div>
      </div>

      <h1 class="login-title">客家金柚<span class="text-gradient">AI智荐</span></h1>
      <p class="login-desc">登录后可享受个性化推荐与浏览历史</p>

      <button class="btn btn-gold btn-lg login-btn" @click="doLogin" :disabled="loading">
        <span v-if="loading" class="loading-spinner"></span>
        {{ loading ? '登录中...' : '🍐 一键登录' }}
      </button>

      <p class="login-note">Web 演示环境使用模拟登录，小程序环境使用微信授权</p>
    </div>
  </div>
</template>

<style scoped>
.login-page {
  display: flex; justify-content: center; align-items: center;
  min-height: calc(100vh - 200px); min-height: calc(100dvh - 200px);
}
.login-card {
  text-align: center; max-width: 400px; width: 100%;
  padding: 48px 36px;
}
.login-logo { margin-bottom: 24px; }
.login-title {
  font-family: var(--font-heading); font-size: 1.8rem; font-weight: 900;
  color: var(--text-heading); margin-bottom: 12px; letter-spacing: .04em;
}
.login-desc { color: var(--text-placeholder); margin-bottom: 32px; font-size: 14px; }
.login-btn { width: 100%; padding: 16px; font-size: 16px; }
.login-note { margin-top: 20px; font-size: 12px; color: var(--text-placeholder); line-height: 1.6; }

.loading-spinner {
  width: 18px; height: 18px; border: 2px solid rgba(255,255,255,.3);
  border-top-color: #fff; border-radius: 50%; animation: spin .6s linear infinite;
  display: inline-block;
}
@keyframes spin { to { transform: rotate(360deg); } }
</style>
