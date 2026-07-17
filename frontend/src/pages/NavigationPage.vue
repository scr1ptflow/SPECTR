<script setup lang="ts">
import { computed } from 'vue'
import { useNavigationStore } from '@/stores/navigation'
import DepartmentHeader from '@/components/DepartmentHeader.vue'
import OfficerReport from '@/components/OfficerReport.vue'
import StatisticCard from '@/components/StatisticCard.vue'

const nav = useNavigationStore()
const report = computed(() => nav.report)

const detailStats = computed(() => {
  if (!report.value?.details) return []
  const d = report.value.details
  return [
    { label: 'System', value: d.system || '---' },
    { label: 'Body', value: d.body || '---' },
    { label: 'Body Type', value: d.body_type || '---' },
    { label: 'Faction', value: d.faction || '---' },
    { label: 'Government', value: d.government || '---' },
    { label: 'Economy', value: d.economy || '---' },
    { label: 'Security', value: d.security || '---' },
    { label: 'Population', value: d.population?.toLocaleString() || '0' },
    { label: 'Station', value: d.station || 'None' },
    { label: 'Station Type', value: d.station_type || '---' },
    { label: 'Docked', value: d.docked ? 'YES' : 'NO' },
    { label: 'Distance from Star', value: d.distance_from_star_ls ? `${d.distance_from_star_ls.toFixed(1)} LS` : '---' },
  ]
})

const historyStats = computed(() => {
  if (!report.value?.history) return []
  const h = report.value.history
  return [
    { label: 'Jumps', value: String(h.jumps) },
    { label: 'Distance', value: `${h.total_distance_ly.toFixed(1)} LY` },
    { label: 'Bodies Scanned', value: String(h.bodies_scanned) },
    { label: 'Bodies Detailed', value: String(h.bodies_detailed) },
    { label: 'Organic Scans', value: String(h.organic_scans) },
  ]
})
</script>

<template>
  <div>
    <DepartmentHeader
      v-if="report"
      :title="report.title"
      subtitle="Where are we, and what is worth doing here?"
    />

    <div v-if="report" class="nav-content">
      <!-- Officer Report -->
      <OfficerReport
        :title="report.title"
        :status="report.status"
        :summary="report.summary"
        :findings="report.findings"
        :recommendations="report.recommendations"
        :generated="report.generated"
      />

      <!-- Details -->
      <div class="nav-section">
        <h3 class="section-title">DETAILS</h3>
        <StatisticCard :items="detailStats" />
      </div>

      <!-- History -->
      <div class="nav-section">
        <h3 class="section-title">HISTORY</h3>
        <StatisticCard :items="historyStats" />
      </div>
    </div>

    <div v-else class="loading text-muted">No navigation data</div>
  </div>
</template>

<style scoped>
.nav-content {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xl);
}

.nav-section {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.section-title {
  font-size: var(--font-size-xs);
  text-transform: uppercase;
  letter-spacing: 2px;
  color: var(--color-primary);
}

.loading {
  display: flex;
  justify-content: center;
  padding: var(--spacing-xl);
  color: var(--color-text-muted);
}
</style>
