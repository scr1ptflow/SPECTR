<script setup lang="ts">
defineProps<{
  items: { label: string; value: string | number; color?: string }[]
}>()
</script>

<template>
  <div class="stat-grid">
    <div v-for="item in items" :key="item.label" class="stat-item">
      <span class="stat-label text-muted">{{ item.label }}</span>
      <span class="stat-value" :style="{ color: item.color || 'var(--color-text)' }">
        {{ item.value }}
      </span>
    </div>
  </div>
</template>

<style scoped>
.stat-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
  gap: var(--spacing-sm);
}
.stat-item {
  background: var(--color-panel);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  padding: var(--spacing-sm) var(--spacing-md);
  display: flex;
  flex-direction: column;
}
.stat-label {
  font-size: var(--font-size-xs);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}
.stat-value {
  font-size: var(--font-size-md);
  font-weight: 700;
  margin-top: 2px;
}
</style>
