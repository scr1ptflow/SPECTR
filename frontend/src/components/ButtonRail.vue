<script setup lang="ts">
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()

defineProps<{
  items: { path: string; label: string; icon: string }[]
  position: 'left' | 'right'
}>()

function isActive(path: string): boolean {
  if (path === '/') return route.path === '/'
  return route.path.startsWith(path)
}
</script>

<template>
  <nav class="rail" :class="`rail-${position}`">
    <div class="rail-items">
      <button
        v-for="item in items"
        :key="item.path"
        class="rail-item"
        :class="{ active: isActive(item.path) }"
        @click="router.push(item.path)"
      >
        <span class="rail-icon">{{ item.icon }}</span>
        <span class="rail-label">{{ item.label }}</span>
      </button>
    </div>
  </nav>
</template>

<style scoped>
.rail {
  display: flex;
  flex-direction: column;
  background: var(--color-panel);
  width: 140px;
}

.rail-left {
  border-right: 1px solid var(--color-border);
}

.rail-right {
  border-left: 1px solid var(--color-border);
}

.rail-items {
  flex: 1;
  padding: var(--spacing-sm);
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.rail-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding: 10px var(--spacing-md);
  border: none;
  background: transparent;
  color: var(--color-text-dim);
  font-family: var(--font-mono);
  font-size: var(--font-size-xs);
  cursor: pointer;
  border-radius: var(--radius-sm);
  transition: all var(--animation-fast);
  text-align: left;
  width: 100%;
  white-space: nowrap;
}

.rail-item:hover {
  background: var(--color-panel-hover);
  color: var(--color-text);
}

.rail-item.active {
  background: rgba(245, 166, 35, 0.1);
  color: var(--color-primary);
}

.rail-left .rail-item.active {
  border-left: 2px solid var(--color-primary);
}

.rail-right .rail-item.active {
  border-right: 2px solid var(--color-primary);
  text-align: right;
  justify-content: flex-end;
}

.rail-icon {
  width: 18px;
  text-align: center;
  font-size: var(--font-size-sm);
}

.rail-label {
  text-transform: uppercase;
  letter-spacing: 0.5px;
}
</style>
