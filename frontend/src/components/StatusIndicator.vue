<script setup lang="ts">
const props = defineProps<{
  status: string
  size?: 'sm' | 'md'
}>()

const statusColors: Record<string, string> = {
  GREEN: 'var(--color-success)',
  BLUE: 'var(--color-secondary)',
  YELLOW: 'var(--color-warning)',
  ORANGE: 'var(--color-primary)',
  RED: 'var(--color-danger)',
}

const color = statusColors[props.status] || 'var(--color-text-muted)'
</script>

<template>
  <span class="status-indicator" :class="[`size-${size || 'md'}`]">
    <span class="status-dot" :style="{ background: color }"></span>
    <span class="status-label" :style="{ color }">{{ status }}</span>
  </span>
</template>

<style scoped>
.status-indicator {
  display: inline-flex;
  align-items: center;
  gap: var(--spacing-xs);
  font-family: var(--font-mono);
  text-transform: uppercase;
  letter-spacing: 1px;
  font-weight: 700;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
  animation: pulse 2s ease-in-out infinite;
}

.size-sm .status-dot {
  width: 6px;
  height: 6px;
}

.size-sm .status-label {
  font-size: var(--font-size-xs);
}

.size-md .status-label {
  font-size: var(--font-size-sm);
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}
</style>
