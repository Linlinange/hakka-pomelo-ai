import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { api } from '../api/request'

export const useUserStore = defineStore('user', () => {
  const token = ref(localStorage.getItem('token') || '')
  const userId = ref(localStorage.getItem('userId') || '')
  const nickname = ref(localStorage.getItem('nickname') || '')
  const avatarUrl = ref(localStorage.getItem('avatarUrl') || '')

  const isLogin = computed(() => !!token.value)

  async function login(code) {
    const data = await api.login(code)
    token.value = data.token
    userId.value = String(data.userId)
    nickname.value = data.nickname || '金柚爱好者'
    avatarUrl.value = data.avatarUrl || ''
    localStorage.setItem('token', data.token)
    localStorage.setItem('userId', String(data.userId))
    localStorage.setItem('nickname', data.nickname || '')
    localStorage.setItem('avatarUrl', data.avatarUrl || '')
  }

  function logout() {
    token.value = ''
    userId.value = ''
    nickname.value = ''
    avatarUrl.value = ''
    localStorage.removeItem('token')
    localStorage.removeItem('userId')
    localStorage.removeItem('nickname')
    localStorage.removeItem('avatarUrl')
  }

  return { token, userId, nickname, avatarUrl, isLogin, login, logout }
})
