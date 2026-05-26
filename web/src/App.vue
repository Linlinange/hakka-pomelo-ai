<script setup>
import { useRoute } from 'vue-router'
import { useUserStore } from './stores/user'

const route = useRoute()
const user = useUserStore()

const tabs = [
  { path: '/',       label: '首页',   icon: '🍊' },
  { path: '/chat',   label: 'AI智荐', icon: '🤖' },
  { path: '/content',label: '文案',   icon: '✍️' },
  { path: user.isLogin ? '/profile' : '/login', label: '我的', icon: '👤' },
]
</script>

<template>
  <div class="app-shell">
    <header class="nav-top">
      <router-link to="/" class="brand">
        <img src="/logo.png" alt="Logo" class="brand-logo" />
        <span class="brand-name">客家金柚<span class="brand-accent">AI</span>智荐</span>
      </router-link>
      <router-link to="/admin" class="nav-icon">⚙️</router-link>
    </header>

    <main class="main-view">
      <router-view v-slot="{ Component }">
        <transition name="page" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </main>

    <nav class="tab-bar">
      <router-link v-for="t in tabs" :key="t.path" :to="t.path"
        class="tab-item" :class="{ active: route.path === t.path }">
        <span class="tab-icon">{{ t.icon }}</span>
        <span class="tab-label">{{ t.label }}</span>
      </router-link>
    </nav>
  </div>
</template>

<style>
@import './assets/hakka-theme.css';

.app-shell { min-height: 100vh; display: flex; flex-direction: column; background: var(--bg-paper); }
.nav-top {
  display: flex; align-items: center; justify-content: space-between;
  padding: 0 20px; height: 56px; position: sticky; top: 0; z-index: 100;
  background: rgba(254,252,247,0.85); backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px); border-bottom: 1px solid var(--border-light);
}
.brand { display: flex; align-items: center; gap: 10px; text-decoration: none; }
.brand-logo { width: 32px; height: 32px; border-radius: 8px; }
.brand-name { font-family: var(--font-heading); font-size: 17px; font-weight: 700; color: var(--text-heading); letter-spacing: .04em; }
.brand-accent { color: var(--primary); font-size: .8em; }
.nav-icon { display: flex; align-items: center; justify-content: center; width: 36px; height: 36px; border-radius: 50%; text-decoration: none; font-size: 18px; }
.nav-icon:hover { background: var(--bg-warm); }
.main-view { flex: 1; max-width: 720px; width: 100%; margin: 0 auto; padding: 20px 16px 0; }

.tab-bar {
  display: flex; justify-content: space-around; align-items: center;
  height: 60px; padding-bottom: env(safe-area-inset-bottom);
  background: rgba(255,255,255,0.9); backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px); border-top: 1px solid var(--border-light);
  position: sticky; bottom: 0; z-index: 100;
}
.tab-item { display: flex; flex-direction: column; align-items: center; gap: 2px; text-decoration: none; padding: 6px 16px; }
.tab-icon { font-size: 22px; }
.tab-label { font-size: 11px; color: var(--text-placeholder); font-weight: 500; }
.tab-item.active .tab-label { color: var(--primary); font-weight: 700; }

.page-enter-active,.page-leave-active{transition:all .25s ease}
.page-enter-from{opacity:0;transform:translateY(12px)}
.page-leave-to{opacity:0;transform:translateY(-12px)}
</style>
