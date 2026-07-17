<script setup lang="ts">
export interface Recommendation {
  priority: string
  message: string
  reason: string
  action: string
}

defineProps<{
  recommendations: Recommendation[]
}>()

const priorityColors: Record<string, string> = {
  critical: 'var(--color-danger)',
  high: 'var(--color-warning)',
  medium: 'var(--color-primary)',
  low: 'var(--color-text-dim)',
}
</script>

<template>
  <div class="recommendation-panel" v-if="recommendations.length">
    <h3 class="panel-title">RECOMMENDATIONS</h3>
    <div class="rec-list">
      <div
        v-for="(rec, i) in recommendations"
        :key="i"
        class="rec-item"
      >
        <div class="rec-header">
          <span
            class="rec-priority"
            :style="{ color: priorityColors[rec.priority] || 'var(--color-text-dim)' }"
          >
            {{ rec.priority.toUpperCase() }}
          </span>
          <span class="rec-message">{{ rec.message }}</span>
        </div>
        <div class="rec-reason text-dim">{{ rec.reason }}</div>
        <div class="rec-action">{{ rec.action }}</div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.recommendation-panel {
  background: var(--color-panel);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: var(--spacing-md);
}

.panel-title {
  font-size: var(--font-size-xs);
  text-transform: uppercase;
  letter-spacing: 2px;
  color: var(--color-primary);
  margin-bottom: var(--spacing-md);
}

.rec-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.rec-item {
  padding: var(--spacing-sm);
  border-left: 2px solid var(--color-border);
  padding-left: var(--spacing-md);
}

.rec-header {
  display: flex;
  align-items: baseline;
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-xs);
}

.rec-priority {
  font-size: var(--font-size-xs);
  font-weight: 700;
  letter-spacing: 1px;
  flex-shrink: 0;
}

.rec-message {
  font-size: var(--font-size-md);
  font-weight: 600;
}

.rec-reason {
  font-size: var(--font-size-xs);
  margin-bottom: var(--spacing-xs);
}

.rec-action {
  font-size: var(--font-size-sm);
  color: var(--color-secondary);
}
</style>
