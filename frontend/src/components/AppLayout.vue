<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const activePath = computed(() => route.path)
const menus = [
  { path: '/', label: '首页' },
  { path: '/resume', label: '简历分析' },
  { path: '/interview', label: 'AI面试' },
  { path: '/report', label: '评估报告' },
]
</script>

<template>
  <div class="app-shell">
    <header class="topbar">
      <router-link to="/" class="brand">
        <span class="brand-mark">智</span>
        <span><strong>智面未来</strong><small>CareerLens Agent</small></span>
      </router-link>
      <nav class="menu" aria-label="主导航">
        <router-link v-for="item in menus" :key="item.path" :to="item.path" :class="{ active: activePath === item.path }">
          {{ item.label }}
        </router-link>
      </nav>
      <router-link to="/resume"><el-button type="primary" round>开始测评</el-button></router-link>
    </header>
    <router-view />
  </div>
</template>

<style scoped>
.app-shell { min-height: 100vh; }
.topbar { position: sticky; top: 0; z-index: 50; height: 72px; padding: 0 max(5vw, 24px); display: grid; grid-template-columns: 1fr auto 1fr; align-items: center; border-bottom: 1px solid var(--line); background: rgba(255,255,255,.88); backdrop-filter: blur(18px); }
.brand { display: flex; align-items: center; gap: 11px; width: max-content; }
.brand-mark { display: grid; place-items: center; width: 38px; height: 38px; border-radius: 12px; color: #fff; font-weight: 800; background: var(--gradient); box-shadow: 0 8px 22px rgba(49, 96, 246, .28); }
.brand strong, .brand small { display: block; }
.brand strong { font-size: 16px; letter-spacing: .04em; }
.brand small { margin-top: 2px; color: var(--muted); font-size: 9px; letter-spacing: .08em; }
.menu { display: flex; align-self: stretch; gap: 36px; }
.menu a { position: relative; display: grid; place-items: center; color: #667085; font-size: 14px; }
.menu a::after { position: absolute; bottom: 0; left: 50%; width: 0; height: 3px; border-radius: 4px; background: var(--primary); content: ''; transition: .25s; }
.menu a.active { color: var(--primary); font-weight: 700; }
.menu a.active::after { left: 15%; width: 70%; }
.topbar > :last-child { justify-self: end; }
@media (max-width: 760px) { .topbar { grid-template-columns: 1fr auto; } .menu { position: fixed; bottom: 0; left: 0; right: 0; height: 62px; justify-content: space-around; gap: 0; background: #fff; border-top: 1px solid var(--line); } .menu a { flex: 1; font-size: 12px; } .topbar > :last-child { display: none; } }
</style>

