<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useArchiveStore } from '@/stores/archive'
import OfficerReport from '@/components/OfficerReport.vue'

const archiveStore = useArchiveStore()
const report = computed(() => archiveStore.archive)

onMounted(() => {
  archiveStore.fetch()
})
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
      <h3 class="section-title">SESSION STATISTICS</h3>

      <div class="stats-grid">
        <div class="stat-card">
          <span class="stat-label text-dim">Jumps</span>
          <span class="stat-value">{{ report.details.jumps }}</span>
        </div>
        <div class="stat-card">
          <span class="stat-label text-dim">Distance</span>
          <span class="stat-value">{{ report.details.total_distance_ly.toFixed(1) }} LY</span>
        </div>
        <div class="stat-card">
          <span class="stat-label text-dim">Bodies Scanned</span>
          <span class="stat-value">{{ report.details.bodies_scanned }}</span>
        </div>
        <div class="stat-card">
          <span class="stat-label text-dim">Organic Samples</span>
          <span class="stat-value">{{ report.details.organic_scans }}</span>
        </div>
        <div class="stat-card">
          <span class="stat-label text-dim">Missions Completed</span>
          <span class="stat-value">{{ report.details.missions_completed }}</span>
        </div>
        <div class="stat-card">
          <span class="stat-label text-dim">Missions Active</span>
          <span class="stat-value">{{ report.details.missions_active }}</span>
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
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: var(--spacing-sm);
}
.stat-card {
  background: var(--color-panel);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  padding: var(--spacing-md);
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
}
.stat-label {
  font-size: var(--font-size-xs);
  text-transform: uppercase;
  letter-spacing: 1px;
}
.stat-value {
  font-size: var(--font-size-lg);
  font-weight: 700;
  color: var(--color-primary);
}
</style>
