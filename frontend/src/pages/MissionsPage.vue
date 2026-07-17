<script setup lang="ts">
import { computed } from 'vue'
import { useMissionStore } from '@/stores/missions'
import OfficerReport from '@/components/OfficerReport.vue'

const missionStore = useMissionStore()
const report = computed(() => missionStore.missions)
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
      <h3 class="section-title">MISSION DETAILS</h3>

      <div v-if="report.details.active?.length" class="detail-group">
        <h4 class="group-label text-primary">Active Missions</h4>
        <div class="item-list">
          <div v-for="m in report.details.active" :key="m.MissionID" class="item-card">
            <span class="item-name">{{ m.Type || m.Type_Localised || 'Unknown' }}</span>
            <span class="item-detail text-dim" v-if="m.Expiry">
              Expires: {{ new Date(m.Expiry).toLocaleDateString() }}
            </span>
          </div>
        </div>
      </div>

      <div v-if="report.details.complete?.length" class="detail-group">
        <h4 class="group-label text-secondary">Completed Missions</h4>
        <div class="item-list">
          <div v-for="m in report.details.complete" :key="m.MissionID" class="item-card">
            <span class="item-name">{{ m.Type || m.Type_Localised || 'Unknown' }}</span>
          </div>
        </div>
      </div>

      <div class="detail-group">
        <h4 class="group-label text-muted">Cargo Hold</h4>
        <div class="cargo-info text-dim">
          {{ report.details.cargo_count }} / {{ report.details.cargo_capacity }} tonnes
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
.cargo-info {
  font-size: var(--font-size-sm);
}
</style>
