<script setup lang="ts">
import { useBridgeStore } from '@/stores/bridge'
import { computed } from 'vue'

const bridge = useBridgeStore()

const system = computed(() => bridge.report?.current_location?.system || '---')
const ship = computed(() => bridge.report?.ship_status?.ship_type || '---')
const credits = computed(() => '---')
const timestamp = computed(() => {
  if (!bridge.lastUpdate) return ''
  return new Date(bridge.lastUpdate).toLocaleTimeString()
})
</script>

<template>
  <footer class="status-bar">
    <span class="status-item">
      <span class="text-muted">SYS:</span> {{ system }}
    </span>
    <span class="status-item">
      <span class="text-muted">SHIP:</span> {{ ship }}
    </span>
    <span class="status-item">
      <span class="text-muted">CR:</span> <span class="text-primary">{{ credits }}</span>
    </span>
    <span class="status-item status-right text-muted">
      {{ timestamp }}
    </span>
  </footer>
</template>

<style scoped>
.status-bar {
  grid-column: 1 / -1;
  background: var(--color-panel);
  border-top: 1px solid var(--color-border);
  display: flex;
  align-items: center;
  padding: 0 var(--spacing-md);
  gap: var(--spacing-lg);
  font-size: var(--font-size-xs);
}
.status-item {
  display: flex;
  gap: var(--spacing-xs);
}
.status-right {
  margin-left: auto;
}
</style>
