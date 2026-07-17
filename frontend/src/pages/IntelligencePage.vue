<script setup lang="ts">
import { computed } from 'vue'
import { useIntelligenceStore } from '@/stores/intelligence'
import OfficerReport from '@/components/OfficerReport.vue'
import StatusIndicator from '@/components/StatusIndicator.vue'

const intelStore = useIntelligenceStore()
const report = computed(() => intelStore.intelligence)

const riskColor = computed(() => {
  const r = report.value?.details?.risk_level || 'low'
  if (r === 'critical') return 'var(--color-danger)'
  if (r === 'high') return 'var(--color-warning)'
  if (r === 'medium') return 'var(--color-primary)'
  return 'var(--color-success)'
})

const highlights = computed(() => report.value?.details?.session_highlights || [])
</script>

<template>
  <div>
    <OfficerReport
      v-if="report"
      :title="report.title"
      :status="report.status"
      :summary="report.summary"
      :findings="report.findings"
      :recommendations="report.recommendations"
      :generated="report.generated"
    />

    <div v-if="report?.details" class="details-section">
      <div class="intel-grid">
        <div class="risk-badge" :style="{ borderColor: riskColor }">
          <span class="risk-label text-muted">THREAT LEVEL</span>
          <span class="risk-value" :style="{ color: riskColor }">
            {{ report.details.risk_level.toUpperCase() }}
          </span>
        </div>

        <div class="highlights-card" v-if="highlights.length">
          <span class="card-label text-muted">HIGHLIGHTS</span>
          <div class="highlight-list">
            <div v-for="(h, i) in highlights" :key="i" class="highlight-item">
              {{ h }}
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.details-section {
  margin-top: var(--spacing-lg);
}
.intel-grid {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: var(--spacing-md);
}
.risk-badge {
  background: var(--color-panel);
  border: 2px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: var(--spacing-md) var(--spacing-lg);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}
.risk-label {
  font-size: var(--font-size-xs);
  letter-spacing: 1px;
}
.risk-value {
  font-size: var(--font-size-xl);
  font-weight: 900;
  letter-spacing: 2px;
}
.highlights-card {
  background: var(--color-panel);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: var(--spacing-md);
}
.card-label {
  font-size: var(--font-size-xs);
  text-transform: uppercase;
  letter-spacing: 1px;
  display: block;
  margin-bottom: var(--spacing-sm);
}
.highlight-list {
  display: flex;
  gap: var(--spacing-sm);
  flex-wrap: wrap;
}
.highlight-item {
  background: rgba(245, 166, 35, 0.1);
  border: 1px solid rgba(245, 166, 35, 0.2);
  border-radius: var(--radius-sm);
  padding: var(--spacing-xs) var(--spacing-sm);
  font-size: var(--font-size-xs);
  color: var(--color-primary);
}
</style>
