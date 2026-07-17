<script setup lang="ts">
import { computed } from 'vue'
import { useNavigationStore } from '@/stores/navigation'
import DepartmentHeader from '@/components/DepartmentHeader.vue'
import OfficerReport from '@/components/OfficerReport.vue'
import StatisticCard from '@/components/StatisticCard.vue'
import StatusIndicator from '@/components/StatusIndicator.vue'
import type { BodyInfo } from '@/api/endpoints'

const nav = useNavigationStore()
const report = computed(() => nav.report)

const systemStats = computed(() => {
  if (!report.value?.details) return []
  const d = report.value.details
  return [
    { label: 'System', value: d.system || '---' },
    { label: 'Faction', value: d.faction || '---' },
    { label: 'Government', value: d.government || '---' },
    { label: 'Economy', value: d.economy || '---' },
    { label: 'Security', value: d.security || '---' },
    { label: 'Allegiance', value: d.allegiance || '---' },
    { label: 'Population', value: d.population?.toLocaleString() || '0' },
    { label: 'Current Body', value: d.body || '---' },
    { label: 'Body Type', value: d.body_type || '---' },
    { label: 'Dist. from Star', value: d.distance_from_star_ls ? `${d.distance_from_star_ls.toFixed(1)} LS` : '---' },
    { label: 'Station', value: d.station || 'None' },
    { label: 'Station Type', value: d.station_type || '---' },
    { label: 'Docked', value: d.docked ? 'YES' : 'NO' },
  ]
})

const bodyCounts = computed(() => {
  if (!report.value?.details?.body_counts) return []
  const bc = report.value.details.body_counts
  return [
    { label: 'Total Bodies', value: String(bc.total) },
    { label: 'Stars', value: String(bc.stars) },
    { label: 'Planets', value: String(bc.planets) },
    { label: 'Moons', value: String(bc.moons) },
    { label: 'Landable', value: String(bc.landable) },
    { label: 'Terraformable', value: String(bc.terraformable) },
    { label: 'Earth-like', value: String(bc.earth_like) },
    { label: 'Water Worlds', value: String(bc.water_worlds) },
    { label: 'Ammonia', value: String(bc.ammonia) },
    { label: 'Gas Giants', value: String(bc.gas_giants) },
  ]
})

const bodies = computed<BodyInfo[]>(() => {
  return report.value?.details?.bodies || []
})

const cartographicValue = computed(() => {
  const val = report.value?.details?.cartographic_estimate || 0
  return val.toLocaleString() + ' CR'
})

const threat = computed(() => {
  return report.value?.details?.threat_assessment || { level: 'UNKNOWN', factors: [], security: '---', notoriety: 0 }
})

const threatColor = computed(() => {
  const map: Record<string, string> = {
    LOW: 'var(--color-success)',
    MEDIUM: 'var(--color-warning)',
    HIGH: 'var(--color-danger)',
  }
  return map[threat.value.level] || 'var(--color-text-muted)'
})

const routeStats = computed(() => {
  if (!report.value?.details) return []
  const d = report.value.details
  const h = report.value.history
  return [
    { label: 'Jumps This Session', value: String(h.jumps) },
    { label: 'Total Distance', value: `${h.total_distance_ly.toFixed(1)} LY` },
    { label: 'Target System', value: d.target_system || 'None' },
    { label: 'Target Body', value: d.target_body || '---' },
    { label: 'Bodies Scanned', value: String(h.bodies_scanned) },
    { label: 'Bodies Mapped', value: String(h.bodies_detailed) },
    { label: 'Organic Samples', value: String(h.organic_scans) },
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
    { label: 'System Bodies', value: String(h.system_bodies) },
  ]
})

function bodyClassColor(body: BodyInfo): string {
  if (body.star_type) return 'var(--color-primary)'
  if (body.body_class.toLowerCase().includes('earthlike')) return 'var(--color-success)'
  if (body.body_class.toLowerCase().includes('water') && !body.body_class.toLowerCase().includes('giant')) return 'var(--color-secondary)'
  if (body.body_class.toLowerCase().includes('ammonia')) return '#ce93d8'
  if (body.terraformable) return 'var(--color-warning)'
  return 'var(--color-text-dim)'
}

function formatTemp(k: number): string {
  if (!k) return '---'
  return `${Math.round(k)} K`
}

function formatDistance(ls: number): string {
  if (!ls) return '---'
  if (ls < 1000) return `${ls.toFixed(1)} LS`
  return `${(ls / 1000).toFixed(1)}k LS`
}
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

      <!-- System Details -->
      <div class="nav-section">
        <h3 class="section-title">SYSTEM DETAILS</h3>
        <StatisticCard :items="systemStats" />
      </div>

      <!-- Threat Assessment -->
      <div class="nav-section">
        <h3 class="section-title">THREAT ASSESSMENT</h3>
        <div class="threat-card">
          <div class="threat-header">
            <span class="threat-label">THREAT LEVEL</span>
            <span class="threat-level" :style="{ color: threatColor }">{{ threat.level }}</span>
          </div>
          <div class="threat-detail text-dim">
            Security: {{ threat.security }} | Notoriety: {{ threat.notoriety }}/10
          </div>
          <div v-if="threat.factors.length" class="threat-factors">
            <div v-for="(factor, i) in threat.factors" :key="i" class="threat-factor">
              <StatusIndicator status="YELLOW" size="sm" />
              <span>{{ factor }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Cartographic Estimate -->
      <div class="nav-section">
        <h3 class="section-title">CARTOGRAPHIC ESTIMATE</h3>
        <div class="carto-card">
          <div class="carto-value">{{ cartographicValue }}</div>
          <div class="carto-label text-dim">Estimated value of remaining scans in this system</div>
        </div>
      </div>

      <!-- Body Catalog -->
      <div class="nav-section" v-if="bodies.length">
        <h3 class="section-title">BODY CATALOG</h3>
        <StatisticCard :items="bodyCounts" />
        <div class="body-list">
          <div
            v-for="(body, i) in bodies"
            :key="i"
            class="body-row"
          >
            <div class="body-name">
              <span class="body-indicator" :style="{ background: bodyClassColor(body) }"></span>
              <span>{{ body.name }}</span>
              <span v-if="body.star_type" class="body-star-type text-muted">{{ body.star_type }}</span>
            </div>
            <div class="body-meta text-dim">
              <span class="body-class">{{ body.body_class }}</span>
              <span v-if="body.distance_ls">{{ formatDistance(body.distance_ls) }}</span>
              <span v-if="body.surface_temp_k">{{ formatTemp(body.surface_temp_k) }}</span>
              <span v-if="body.terraformable" class="body-tag tag-terra">TERRA</span>
              <span v-if="body.landable" class="body-tag tag-land">LAND</span>
              <span v-if="body.scanned" class="body-tag tag-scanned">SCANNED</span>
              <span v-if="body.mapped" class="body-tag tag-mapped">MAPPED</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Route & Session -->
      <div class="nav-section">
        <h3 class="section-title">ROUTE & SESSION</h3>
        <StatisticCard :items="routeStats" />
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

/* Threat Assessment */
.threat-card {
  background: var(--color-panel);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: var(--spacing-md);
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.threat-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.threat-label {
  font-size: var(--font-size-xs);
  text-transform: uppercase;
  letter-spacing: 1px;
  color: var(--color-text-muted);
}

.threat-level {
  font-size: var(--font-size-lg);
  font-weight: 700;
  letter-spacing: 2px;
}

.threat-detail {
  font-size: var(--font-size-xs);
}

.threat-factors {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
  margin-top: var(--spacing-xs);
}

.threat-factor {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  font-size: var(--font-size-xs);
}

/* Cartographic Estimate */
.carto-card {
  background: var(--color-panel);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: var(--spacing-lg);
  text-align: center;
}

.carto-value {
  font-size: var(--font-size-xl);
  font-weight: 700;
  color: var(--color-primary);
}

.carto-label {
  font-size: var(--font-size-xs);
  margin-top: var(--spacing-xs);
}

/* Body Catalog */
.body-list {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.body-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--spacing-sm) var(--spacing-md);
  background: var(--color-panel);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
}

.body-row:hover {
  border-color: var(--color-border-active);
}

.body-name {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  font-weight: 600;
}

.body-indicator {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.body-star-type {
  font-size: var(--font-size-xs);
  font-weight: 400;
}

.body-meta {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  font-size: var(--font-size-xs);
}

.body-class {
  color: var(--color-text-dim);
}

.body-tag {
  padding: 1px 6px;
  border-radius: 3px;
  font-size: 10px;
  font-weight: 600;
  letter-spacing: 0.5px;
  text-transform: uppercase;
}

.tag-terra {
  background: rgba(245, 166, 35, 0.15);
  color: var(--color-primary);
}

.tag-land {
  background: rgba(79, 195, 247, 0.15);
  color: var(--color-secondary);
}

.tag-scanned {
  background: rgba(76, 175, 80, 0.15);
  color: var(--color-success);
}

.tag-mapped {
  background: rgba(206, 147, 216, 0.15);
  color: #ce93d8;
}

.loading {
  display: flex;
  justify-content: center;
  padding: var(--spacing-xl);
  color: var(--color-text-muted);
}
</style>
