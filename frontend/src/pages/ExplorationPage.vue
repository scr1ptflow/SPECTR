<script setup lang="ts">
import { computed } from 'vue'
import { useScanStore } from '@/stores/scans'
import OfficerReport from '@/components/OfficerReport.vue'

const scanStore = useScanStore()
const report = computed(() => scanStore.scans)
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
      <h3 class="section-title">SCAN DATA</h3>

      <div class="detail-group">
        <h4 class="group-label text-primary">Bodies</h4>
        <div class="stat-row">
          <span class="stat-label text-dim">Scanned</span>
          <span class="stat-value">{{ report.details.bodies_scanned }}</span>
        </div>
        <div class="stat-row">
          <span class="stat-label text-dim">Detailed</span>
          <span class="stat-value">{{ report.details.bodies_detailed }}</span>
        </div>
      </div>

      <div class="detail-group">
        <h4 class="group-label text-primary">Exobiology</h4>
        <div class="stat-row">
          <span class="stat-label text-dim">Samples Collected</span>
          <span class="stat-value">{{ report.details.organic_scan_count }}</span>
        </div>
        <div class="stat-row">
          <span class="stat-label text-dim">Unique Species</span>
          <span class="stat-value">{{ report.details.unique_species }}</span>
        </div>
        <div class="stat-row">
          <span class="stat-label text-dim">Data Sold</span>
          <span class="stat-value text-primary">
            {{ report.details.total_earned.toLocaleString() }} CR
          </span>
        </div>
      </div>

      <div v-if="report.details.species?.length" class="detail-group">
        <h4 class="group-label text-secondary">Species Collected</h4>
        <div class="item-list">
          <div v-for="(s, i) in report.details.species" :key="i" class="item-card">
            <span class="item-name">{{ s.species || 'Unknown' }}</span>
            <span class="item-detail text-dim">
              {{ s.variant }} — {{ s.body }} (x{{ s.count }})
            </span>
          </div>
        </div>
      </div>

      <div v-if="report.details.sold?.length" class="detail-group">
        <h4 class="group-label text-secondary">Sold Data</h4>
        <div class="item-list">
          <div v-for="(s, i) in report.details.sold" :key="i" class="item-card">
            <span class="item-name">{{ s.species }}</span>
            <span class="item-detail text-primary">
              {{ s.value.toLocaleString() }} CR (x{{ s.count }})
            </span>
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
.section-title {
  font-size: var(--font-size-xs);
  text-transform: uppercase;
  letter-spacing: 2px;
  color: var(--color-primary);
  margin-bottom: var(--spacing-md);
}
.detail-group {
  margin-bottom: var(--spacing-md);
}
.group-label {
  font-size: var(--font-size-xs);
  text-transform: uppercase;
  letter-spacing: 1px;
  margin-bottom: var(--spacing-sm);
}
.stat-row {
  display: flex;
  justify-content: space-between;
  padding: var(--spacing-xs) 0;
  border-bottom: 1px solid var(--color-border);
}
.stat-label {
  font-size: var(--font-size-xs);
}
.stat-value {
  font-weight: 600;
}
.item-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
}
.item-card {
  background: var(--color-panel);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  padding: var(--spacing-sm) var(--spacing-md);
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.item-name {
  font-weight: 600;
}
.item-detail {
  font-size: var(--font-size-xs);
}
</style>
