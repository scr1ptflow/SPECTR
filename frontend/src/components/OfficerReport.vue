<script setup lang="ts">
import StatusIndicator from './StatusIndicator.vue'
import RecommendationPanel from './RecommendationPanel.vue'
import type { Recommendation } from './RecommendationPanel.vue'

export interface Finding {
  title: string
  description: string
  severity: string
}

defineProps<{
  title: string
  status: string
  summary: string
  findings: Finding[]
  recommendations: Recommendation[]
  generated: string
}>()
</script>

<template>
  <div class="officer-report">
    <div class="report-header">
      <h2 class="report-title">{{ title }}</h2>
      <StatusIndicator :status="status" />
    </div>

    <div class="report-summary">{{ summary }}</div>

    <div class="report-findings" v-if="findings.length">
      <h3 class="section-title">FINDINGS</h3>
      <div class="findings-list">
        <div
          v-for="(finding, i) in findings"
          :key="i"
          class="finding-item"
        >
          <div class="finding-header">
            <StatusIndicator :status="finding.severity" size="sm" />
            <span class="finding-title">{{ finding.title }}</span>
          </div>
          <div class="finding-description text-dim">{{ finding.description }}</div>
        </div>
      </div>
    </div>

    <RecommendationPanel :recommendations="recommendations" />

    <div class="report-generated text-muted">
      Generated: {{ generated }}
    </div>
  </div>
</template>

<style scoped>
.officer-report {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
}

.report-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.report-title {
  font-size: var(--font-size-lg);
  font-weight: 700;
  color: var(--color-primary);
  letter-spacing: 1px;
  text-transform: uppercase;
}

.report-summary {
  font-size: var(--font-size-md);
  line-height: 1.6;
  color: var(--color-text);
  padding: var(--spacing-md);
  background: var(--color-panel);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
}

.section-title {
  font-size: var(--font-size-xs);
  text-transform: uppercase;
  letter-spacing: 2px;
  color: var(--color-primary);
  margin-bottom: var(--spacing-md);
}

.findings-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.finding-item {
  padding: var(--spacing-sm) var(--spacing-md);
  background: var(--color-panel);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
}

.finding-header {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-xs);
}

.finding-title {
  font-weight: 600;
}

.finding-description {
  font-size: var(--font-size-xs);
}

.report-generated {
  font-size: var(--font-size-xs);
  text-align: right;
}
</style>
