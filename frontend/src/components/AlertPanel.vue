<script setup lang="ts">
defineProps<{
  title: string
}>()
</script>

<template>
  <section class="alert-panel">
    <h3 class="panel-title text-warning">{{ title }}</h3>
    <div class="panel-content">
      <slot />
    </div>
  </section>
</template>

<style scoped>
.alert-panel {
  background: rgba(255, 152, 0, 0.05);
  border: 1px solid rgba(255, 152, 0, 0.2);
  border-radius: var(--radius-md);
  padding: var(--spacing-md);
}
.panel-title {
  font-size: var(--font-size-sm);
  font-weight: 600;
  margin-bottom: var(--spacing-sm);
}
.panel-content {
  font-size: var(--font-size-sm);
}
</style>
