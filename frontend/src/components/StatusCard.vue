<script setup lang="ts">
defineProps<{
  label: string
  value: string | number
  color?: string
  icon?: string
}>()
</script>

<template>
  <div class="status-card">
    <div class="card-label text-muted">{{ label }}</div>
    <div class="card-value" :style="{ color: color || 'var(--color-text)' }">
      <span v-if="icon" class="card-icon">{{ icon }}</span>
      {{ value }}
    </div>
  </div>
</template>

<style scoped>
.status-card {
  background: var(--color-panel);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: var(--spacing-md);
  min-width: 120px;
}
.card-label {
  font-size: var(--font-size-xs);
  text-transform: uppercase;
  letter-spacing: 1px;
  margin-bottom: var(--spacing-xs);
}
.card-value {
  font-size: var(--font-size-lg);
  font-weight: 700;
}
.card-icon {
  margin-right: var(--spacing-xs);
}
</style>
