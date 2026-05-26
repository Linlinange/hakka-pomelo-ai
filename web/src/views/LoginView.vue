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
    // Web 环境无法调用 wx.login，使用模拟 code
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
    <div class="card login-card">
      <div class="login-icon">🍊</div>
      <h2>欢迎登录</h2>
      <p class="desc">登录后可享受个性化推荐与浏览历史</p>
      <button class="btn btn-gold" style="width:100%;padding:14px;font-size:16px;" @click="doLogin" :disabled="loading">
        {{ loading ? '登录中...' : '一键登录' }}
      </button>
      <p class="note">Web 演示环境使用模拟登录，小程序环境使用微信授权</p>
    </div>
  </div>
</template>

<style scoped>
.login-page { display: flex; justify-content: center; padding-top: 80px; }
.login-card { text-align: center; max-width: 400px; width: 100%; padding: 40px 32px; }
.login-icon { font-size: 64px; margin-bottom: 16px; }
h2 { margin-bottom: 8px; }
.desc { color: #999; margin-bottom: 28px; font-size: 14px; }
.note { margin-top: 16px; font-size: 12px; color: #bbb; }
</style>
