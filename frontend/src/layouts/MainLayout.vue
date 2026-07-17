<script setup lang="ts">
import { onMounted, onUnmounted } from 'vue'
import { useBridgeStore } from '@/stores/bridge'
import { api } from '@/api/client'
import SidebarNav from '@/components/SidebarNav.vue'
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
</script>

<template>
  <div class="layout">
    <SidebarNav />
    <main class="main-content">
      <router-view />
    </main>
    <StatusBar />
  </div>
</template>

<style scoped>
.layout {
  display: grid;
  grid-template-columns: 200px 1fr;
  grid-template-rows: 1fr 28px;
  height: 100vh;
  overflow: hidden;
}
.main-content {
  overflow-y: auto;
  padding: var(--spacing-md);
  grid-row: 1;
}
</style>
