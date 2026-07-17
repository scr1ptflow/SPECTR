<script setup lang="ts">
import { computed } from 'vue'
import { useEngineeringStore } from '@/stores/engineering'
import DepartmentHeader from '@/components/DepartmentHeader.vue'
import OfficerReport from '@/components/OfficerReport.vue'
import StatisticCard from '@/components/StatisticCard.vue'

const eng = useEngineeringStore()
const report = computed(() => eng.report)

const detailStats = computed(() => {
  if (!report.value?.details) return []
  const d = report.value.details
  return [
    { label: 'Ship Type', value: d.ship_type || '---' },
    { label: 'Ship Name', value: d.ship_name || '---' },
    { label: 'Ship Ident', value: d.ship_ident || '---' },
    { label: 'Hull Health', value: `${d.hull_health.toFixed(0)}%` },
    { label: 'Fuel', value: d.fuel_capacity > 0 ? `${d.fuel_current.toFixed(1)} / ${d.fuel_capacity.toFixed(1)}` : '---' },
    { label: 'Cargo', value: `${d.cargo_count} / ${d.cargo_capacity}` },
    { label: 'Rebuy', value: `${d.rebuy.toLocaleString()} CR` },
    { label: 'Modules', value: String(d.modules.length) },
    { label: 'Engineer', value: d.engineer || 'None' },
    { label: 'Modification', value: d.current_modification || 'None' },
    { label: 'Grade', value: d.grade > 0 ? String(d.grade) : '---' },
    { label: 'Materials', value: `${d.material_count} (${d.material_types} types)` },
  ]
})

const materials = computed(() => {
  if (!report.value?.details) return []
  const m = report.value.details.materials || {}
  return Object.entries(m)
    .map(([name, count]) => ({ name, count }))
    .sort((a, b) => b.count - a.count)
})
</script>

<template>
  <div>
    <DepartmentHeader
      v-if="report"
      :title="report.title"
      subtitle="Can the ship safely continue?"
    />

    <div v-if="report" class="eng-content">
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
      <div class="eng-section">
        <h3 class="section-title">DETAILS</h3>
        <StatisticCard :items="detailStats" />
      </div>

      <!-- Materials -->
      <div v-if="materials.length" class="eng-section">
        <h3 class="section-title">MATERIALS ({{ materials.length }})</h3>
        <div class="material-grid">
          <div v-for="mat in materials" :key="mat.name" class="material-item">
            <span class="mat-name">{{ mat.name }}</span>
            <span class="mat-count text-primary">{{ mat.count }}</span>
          </div>
        </div>
      </div>
    </div>

    <div v-else class="loading text-muted">No engineering data</div>
  </div>
</template>

<style scoped>
.eng-content {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xl);
}

.eng-section {
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

.material-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
  gap: var(--spacing-xs);
}

.material-item {
  background: var(--color-panel);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  padding: var(--spacing-sm);
  display: flex;
  justify-content: space-between;
}

.mat-name {
  font-size: var(--font-size-sm);
}

.mat-count {
  font-weight: 700;
}

.loading {
  display: flex;
  justify-content: center;
  padding: var(--spacing-xl);
}
</style>
