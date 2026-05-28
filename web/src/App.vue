<script setup>
import { useRoute } from 'vue-router'
import { useUserStore } from './stores/user'

const route = useRoute()
const user = useUserStore()

const tabs = [
  { path: '/',       label: '首页', icon: '🏠' },
  { path: '/chat',   label: 'AI智荐', icon: '🤖' },
  { path: '/content',label: '文案', icon: '✍️' },
  { path: user.isLogin ? '/profile' : '/login', label: '我的', icon: '👤' },
]
</script>

<template>
  <div class="app-shell">
    <!-- 顶部导航 -->
    <header class="nav-top">
      <router-link to="/" class="brand">
        <div class="brand-icon">🍐</div>
        <div class="brand-text">
          <span class="brand-name">客家金柚</span>
          <span class="brand-accent">AI智荐</span>
        </div>
      </router-link>
      <div class="nav-actions">
        <router-link to="/admin" class="nav-btn" title="管理">⚙️</router-link>
      </div>
    </header>

    <!-- 主内容 -->
    <main class="main-view">
      <router-view v-slot="{ Component }">
        <transition name="page" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </main>

    <!-- 底部标签栏 -->
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

.app-shell {
  min-height: 100vh; min-height: 100dvh;
  display: flex; flex-direction: column;
  background: var(--bg-paper);
}

/* === 顶栏 === */
.nav-top {
  display: flex; align-items: center; justify-content: space-between;
  padding: 0 20px; height: 56px;
  position: sticky; top: 0; z-index: 100;
  background: rgba(254,252,247,0.85);
  backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px);
  border-bottom: 1px solid var(--border-light);
}
.brand { display: flex; align-items: center; gap: 10px; text-decoration: none; }
.brand-icon {
  width: 36px; height: 36px; border-radius: var(--radius-sm);
  background: linear-gradient(135deg, var(--gold-light), #fef7ee);
  display: flex; align-items: center; justify-content: center;
  font-size: 20px; box-shadow: var(--shadow-xs);
}
.brand-text { display: flex; align-items: baseline; gap: 6px; }
.brand-name {
  font-family: var(--font-heading); font-size: 17px; font-weight: 700;
  color: var(--text-heading); letter-spacing: .04em;
}
.brand-accent {
  font-size: 11px; font-weight: 700; color: #fff;
  background: var(--primary); padding: 2px 8px; border-radius: var(--radius-xs);
  letter-spacing: .06em;
}
.nav-actions { display: flex; gap: 4px; }
.nav-btn {
  width: 36px; height: 36px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  text-decoration: none; font-size: 18px; transition: all .2s;
}
.nav-btn:hover { background: var(--bg-warm); }

/* === 主内容区 === */
.main-view {
  flex: 1; width: 100%; max-width: 720px;
  margin: 0 auto; padding: 20px 16px 0;
}

/* === 底部标签 === */
.tab-bar {
  display: flex; justify-content: space-around; align-items: center;
  height: 64px; padding-bottom: env(safe-area-inset-bottom);
  background: rgba(255,255,255,0.9);
  backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px);
  border-top: 1px solid var(--border-light);
  position: sticky; bottom: 0; z-index: 100;
}
.tab-item {
  display: flex; flex-direction: column; align-items: center; gap: 2px;
  text-decoration: none; padding: 6px 18px; transition: all .2s;
}
.tab-icon { font-size: 22px; transition: transform .2s; }
.tab-label { font-size: 11px; color: var(--text-placeholder); font-weight: 500; transition: color .2s; }
.tab-item.active .tab-label { color: var(--primary); font-weight: 700; }
.tab-item.active .tab-icon { transform: scale(1.1); }
.tab-item:active .tab-icon { transform: scale(.9); }

/* === 页面过渡 === */
.page-enter-active, .page-leave-active { transition: all .25s var(--ease-out); }
.page-enter-from { opacity: 0; transform: translateY(12px); }
.page-leave-to { opacity: 0; transform: translateY(-12px); }
</style>
