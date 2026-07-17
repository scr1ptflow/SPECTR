<script setup lang="ts">
import { onMounted, onUnmounted } from 'vue'
import { useBridgeStore } from '@/stores/bridge'
import { api } from '@/api/client'
import ButtonRail from '@/components/ButtonRail.vue'
import StatusBar from '@/components/StatusBar.vue'

const bridge = useBridgeStore()

let unsubscribe: (() => void) | null = null

onMounted(async () => {
  await bridge.fetchState()
  api.connectWebSocket()
  unsubscribe = api.onStateUpdate((data) => bridge.updateFromWebSocket(data))
})

onUnmounted(() => {
  unsubscribe?.()
})

const leftItems = [
  { path: '/', label: 'Bridge', icon: '◈' },
  { path: '/navigation', label: 'Navigation', icon: '◎' },
  { path: '/ship', label: 'Ship', icon: '◇' },
  { path: '/engineering', label: 'Engineering', icon: '⚙' },
  { path: '/commander', label: 'Commander', icon: '⊕' },
]

const rightItems = [
  { path: '/missions', label: 'Missions', icon: '☰' },
  { path: '/exploration', label: 'Exploration', icon: '✧' },
  { path: '/intelligence', label: 'Intelligence', icon: '◉' },
  { path: '/archive', label: 'Archive', icon: '▤' },
  { path: '/settings', label: 'Settings', icon: '⚙' },
]
</script>

<template>
  <div class="layout">
    <ButtonRail :items="leftItems" position="left" />

    <div class="center">
      <header class="center-header">
        <span class="app-title text-primary">SPECTR</span>
        <div class="connection-badge" :class="{ online: bridge.connected }">
          <span class="status-dot"></span>
        </div>
      </header>
      <main class="center-content">
        <router-view />
      </main>
    </div>

    <ButtonRail :items="rightItems" position="right" />

    <StatusBar />
  </div>
</template>

<style scoped>
.layout {
  display: grid;
  grid-template-columns: 140px 1fr 140px;
  grid-template-rows: 1fr 28px;
  height: 100vh;
  overflow: hidden;
}

.center {
  display: flex;
  flex-direction: column;
  overflow: hidden;
  grid-column: 2;
  grid-row: 1;
}

.center-header {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-lg);
  padding: var(--spacing-sm) var(--spacing-md);
  border-bottom: 1px solid var(--color-border);
  background: var(--color-panel);
  flex-shrink: 0;
}

.app-title {
  font-size: var(--font-size-sm);
  font-weight: 700;
  letter-spacing: 3px;
}

.connection-badge {
  display: flex;
  align-items: center;
}

.status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--color-danger);
}

.connection-badge.online .status-dot {
  background: var(--color-success);
}

.center-content {
  flex: 1;
  overflow-y: auto;
  padding: var(--spacing-md);
}
</style>
