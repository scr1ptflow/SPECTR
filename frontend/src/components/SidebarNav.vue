<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useBridgeStore } from '@/stores/bridge'

const route = useRoute()
const router = useRouter()
const bridge = useBridgeStore()

const navItems = [
  { path: '/', label: 'Bridge', icon: '◈' },
  { path: '/navigation', label: 'Navigation', icon: '◎' },
  { path: '/ship', label: 'Ship', icon: '◇' },
  { path: '/engineering', label: 'Engineering', icon: '⚙' },
  { path: '/missions', label: 'Missions', icon: '☰' },
  { path: '/exploration', label: 'Exploration', icon: '✧' },
  { path: '/commander', label: 'Commander', icon: '⊕' },
  { path: '/intelligence', label: 'Intelligence', icon: '◉' },
  { path: '/archive', label: 'Archive', icon: '▤' },
]

function isActive(path: string): boolean {
  if (path === '/') return route.path === '/'
  return route.path.startsWith(path)
}
</script>

<template>
  <nav class="sidebar">
    <div class="sidebar-header">
      <span class="logo text-primary">ELITE BRIDGE</span>
    </div>
    <div class="nav-items">
      <button
        v-for="item in navItems"
        :key="item.path"
        class="nav-item"
        :class="{ active: isActive(item.path) }"
        @click="router.push(item.path)"
      >
        <span class="nav-icon">{{ item.icon }}</span>
        <span class="nav-label">{{ item.label }}</span>
      </button>
    </div>
    <div class="sidebar-footer">
      <div class="connection-status" :class="{ online: bridge.connected }">
        <span class="status-dot"></span>
        {{ bridge.connected ? 'ONLINE' : 'OFFLINE' }}
      </div>
    </div>
  </nav>
</template>

<style scoped>
.sidebar {
  background: var(--color-panel);
  border-right: 1px solid var(--color-border);
  display: flex;
  flex-direction: column;
  grid-row: 1;
}
.sidebar-header {
  padding: var(--spacing-md);
  border-bottom: 1px solid var(--color-border);
}
.logo {
  font-size: var(--font-size-sm);
  font-weight: 700;
  letter-spacing: 2px;
}
.nav-items {
  flex: 1;
  padding: var(--spacing-sm);
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.nav-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-sm) var(--spacing-md);
  border: none;
  background: transparent;
  color: var(--color-text-dim);
  font-family: var(--font-mono);
  font-size: var(--font-size-sm);
  cursor: pointer;
  border-radius: var(--radius-sm);
  transition: all var(--animation-fast);
  text-align: left;
  width: 100%;
}
.nav-item:hover {
  background: var(--color-panel-hover);
  color: var(--color-text);
}
.nav-item.active {
  background: rgba(245, 166, 35, 0.1);
  color: var(--color-primary);
  border-left: 2px solid var(--color-primary);
}
.nav-icon {
  width: 20px;
  text-align: center;
}
.sidebar-footer {
  padding: var(--spacing-md);
  border-top: 1px solid var(--color-border);
}
.connection-status {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  font-size: var(--font-size-xs);
  color: var(--color-danger);
}
.connection-status.online {
  color: var(--color-success);
}
.status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: currentColor;
}
</style>
