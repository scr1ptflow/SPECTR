<script setup lang="ts">
import { computed } from 'vue'
import { useCommanderStore } from '@/stores/commander'
import DepartmentHeader from '@/components/DepartmentHeader.vue'
import OfficerReport from '@/components/OfficerReport.vue'
import StatisticCard from '@/components/StatisticCard.vue'
import ProgressRing from '@/components/ProgressRing.vue'

const cmdr = useCommanderStore()
const report = computed(() => cmdr.report)

const detailStats = computed(() => {
  if (!report.value?.details) return []
  const d = report.value.details
  return [
    { label: 'Commander', value: d.name || '---' },
    { label: 'Credits', value: `${d.credits.toLocaleString()} CR` },
    { label: 'Loan', value: d.loan > 0 ? `${d.loan.toLocaleString()} CR` : 'None' },
    { label: 'Squadron', value: d.squadron || 'None' },
    { label: 'Powerplay', value: d.powerplay_power || 'None' },
    { label: 'PP Rank', value: d.powerplay_rank > 0 ? String(d.powerplay_rank) : '---' },
    { label: 'PP Merits', value: d.powerplay_merits > 0 ? d.powerplay_merits.toLocaleString() : '---' },
  ]
})

const careerRanks = computed(() => {
  if (!report.value?.details?.ranks) return []
  const r = report.value.details.ranks
  return ['combat', 'trade', 'explore'].map(cat => ({
    category: cat,
    name: r[cat]?.name || 'Unknown',
    level: r[cat]?.level || 0,
    progress: r[cat]?.progress || 0,
  }))
})

const otherRanks = computed(() => {
  if (!report.value?.details?.ranks) return []
  const r = report.value.details.ranks
  return ['empire', 'federation', 'cqc', 'soldier', 'exobiologist'].map(cat => ({
    category: cat,
    name: r[cat]?.name || 'Unknown',
    level: r[cat]?.level || 0,
    progress: r[cat]?.progress || 0,
  }))
})
</script>

<template>
  <div>
    <DepartmentHeader
      v-if="report"
      :title="report.title"
      subtitle="What is the commander's current status?"
    />

    <div v-if="report" class="cmdr-content">
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
      <div class="cmdr-section">
        <h3 class="section-title">DETAILS</h3>
        <StatisticCard :items="detailStats" />
      </div>

      <!-- Career Ranks -->
      <div v-if="careerRanks.length" class="cmdr-section">
        <h3 class="section-title">CAREER RANKS</h3>
        <div class="rank-grid">
          <div v-for="rank in careerRanks" :key="rank.category" class="rank-card">
            <ProgressRing
              :label="rank.category"
              :value="rank.progress"
              :color="
                rank.category === 'combat' ? 'var(--color-danger)' :
                rank.category === 'trade' ? 'var(--color-primary)' :
                'var(--color-secondary)'
              "
            />
            <span class="rank-name">{{ rank.name }}</span>
          </div>
        </div>
      </div>

      <!-- Other Ranks -->
      <div v-if="otherRanks.length" class="cmdr-section">
        <h3 class="section-title">FACTION & SPECIALTY RANKS</h3>
        <div class="other-ranks">
          <div v-for="rank in otherRanks" :key="rank.category" class="other-rank">
            <span class="rank-label text-dim">{{ rank.category }}</span>
            <span class="rank-value">{{ rank.name }}</span>
          </div>
        </div>
      </div>
    </div>

    <div v-else class="loading text-muted">No commander data</div>
  </div>
</template>

<style scoped>
.cmdr-content {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xl);
}

.cmdr-section {
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

.rank-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--spacing-md);
}

.rank-card {
  background: var(--color-panel);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: var(--spacing-md);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--spacing-sm);
}

.rank-name {
  font-weight: 700;
  font-size: var(--font-size-sm);
}

.other-ranks {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: var(--spacing-sm);
}

.other-rank {
  background: var(--color-panel);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  padding: var(--spacing-sm);
  display: flex;
  justify-content: space-between;
}

.rank-label {
  font-size: var(--font-size-xs);
  text-transform: uppercase;
  letter-spacing: 1px;
}

.rank-value {
  font-weight: 700;
}

.loading {
  display: flex;
  justify-content: center;
  padding: var(--spacing-xl);
}
</style>
