<script setup lang="ts">
defineProps<{
  title: string
  subtitle?: string
}>()
</script>

<template>
  <header class="department-header">
    <h1 class="dept-title">{{ title }}</h1>
    <p v-if="subtitle" class="dept-subtitle text-dim">{{ subtitle }}</p>
    <slot />
  </header>
</template>

<style scoped>
.department-header {
  margin-bottom: var(--spacing-lg);
  padding-bottom: var(--spacing-md);
  border-bottom: 1px solid var(--color-border);
}
.dept-title {
  font-size: var(--font-size-xl);
  font-weight: 700;
  color: var(--color-primary);
  letter-spacing: 1px;
}
.dept-subtitle {
  font-size: var(--font-size-sm);
  margin-top: var(--spacing-xs);
}
</style>
