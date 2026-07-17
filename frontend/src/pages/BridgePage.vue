<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useBridgeStore } from '@/stores/bridge'
import StatusIndicator from '@/components/StatusIndicator.vue'
import RecommendationPanel from '@/components/RecommendationPanel.vue'

const bridge = useBridgeStore()

onMounted(() => {
  bridge.fetchState()
})

const briefing = computed(() => bridge.report?.captain_briefing)
const shipStatus = computed(() => bridge.report?.ship_status)
const mission = computed(() => bridge.report?.current_mission)
const departments = computed(() => bridge.report?.department_status || [])
const location = computed(() => bridge.report?.current_location)
const alerts = computed(() => bridge.report?.alerts || [])
const recommendations = computed(() => bridge.report?.recommendations || [])
const expedition = computed(() => bridge.report?.expedition_summary)
const log = computed(() => bridge.report?.captains_log || [])

const deptName = (d: string) => {
  const names: Record<string, string> = {
    navigation: 'NAV',
    engineering: 'ENG',
    laboratory: 'LAB',
    operations: 'OPS',
    tactical: 'TAC',
    communications: 'COM',
    commander: 'CMD',
    archive: 'ARC',
    intelligence: 'INT',
  }
  return names[d] || d.toUpperCase()
}

const severityColor = (s: string) => {
  if (s === 'RED') return 'var(--color-danger)'
  if (s === 'ORANGE') return 'var(--color-warning)'
  if (s === 'YELLOW') return 'var(--color-warning)'
  if (s === 'GREEN') return 'var(--color-success)'
  if (s === 'BLUE') return 'var(--color-secondary)'
  if (s === 'OFFLINE') return 'var(--color-text-muted)'
  return 'var(--color-text-muted)'
}

const deptStatusColor = (s: string) => {
  if (s === 'OFFLINE') return 'var(--color-text-muted)'
  return severityColor(s)
}
</script>

<template>
  <div class="bridge-page" v-if="briefing">
    <!-- 1. Captain's Briefing -->
    <section class="bridge-section briefing-section">
      <div class="section-header">
        <span class="section-label">CAPTAIN'S BRIEFING</span>
        <StatusIndicator v-if="briefing" :status="briefing.status" size="sm" />
      </div>
      <div class="briefing-text" v-if="briefing">
        {{ briefing.summary }}
      </div>
    </section>

    <!-- Main content grid -->
    <div class="bridge-grid">

      <!-- Left column -->
      <div class="bridge-col">

        <!-- 2. Ship Status -->
        <section class="bridge-section" v-if="shipStatus">
          <div class="section-header">
            <span class="section-label">SHIP STATUS</span>
          </div>
          <div class="ship-info">
            <div class="ship-name-line">
              <span class="ship-type">{{ shipStatus.ship_type }}</span>
              <span v-if="shipStatus.ship_name" class="ship-name text-dim">
                "{{ shipStatus.ship_name }}"
              </span>
            </div>
            <div class="ship-metrics">
              <div class="metric">
                <span class="metric-label">HULL</span>
                <div class="metric-bar">
                  <div
                    class="metric-fill"
                    :style="{
                      width: shipStatus.hull_health + '%',
                      background: shipStatus.hull_health > 80 ? 'var(--color-success)'
                        : shipStatus.hull_health > 50 ? 'var(--color-warning)'
                        : 'var(--color-danger)'
                    }"
                  />
                </div>
                <span class="metric-value">{{ shipStatus.hull_health.toFixed(0) }}%</span>
              </div>
              <div class="metric">
                <span class="metric-label">FUEL</span>
                <div class="metric-bar">
                  <div
                    class="metric-fill"
                    :style="{
                      width: shipStatus.fuel_percent + '%',
                      background: shipStatus.fuel_percent > 50 ? 'var(--color-success)'
                        : shipStatus.fuel_percent > 25 ? 'var(--color-warning)'
                        : 'var(--color-danger)'
                    }"
                  />
                </div>
                <span class="metric-value">{{ shipStatus.fuel_percent.toFixed(0) }}%</span>
              </div>
              <div class="metric">
                <span class="metric-label">CARGO</span>
                <div class="metric-bar">
                  <div
                    class="metric-fill"
                    :style="{
                      width: shipStatus.cargo_percent + '%',
                      background: 'var(--color-secondary)'
                    }"
                  />
                </div>
                <span class="metric-value">
                  {{ shipStatus.cargo_count }}/{{ shipStatus.cargo_capacity }}
                </span>
              </div>
            </div>
            <div class="ship-meta text-dim">
              Rebuy: {{ shipStatus.rebuy.toLocaleString() }} CR
            </div>
          </div>
        </section>

        <!-- 3. Current Mission -->
        <section class="bridge-section" v-if="mission">
          <div class="section-header">
            <span class="section-label">CURRENT MISSION</span>
          </div>
          <div class="mission-info">
            <div class="mission-title">{{ mission.title }}</div>
            <div class="mission-details">
              <span v-if="mission.destination" class="text-dim">
                Destination: {{ mission.destination }}
              </span>
              <span v-if="mission.reward" class="text-primary">
                {{ mission.reward.toLocaleString() }} CR
              </span>
            </div>
            <div v-if="mission.expiration" class="mission-expiry text-dim">
              Expires: {{ new Date(mission.expiration).toLocaleString() }}
            </div>
          </div>
        </section>

        <!-- 6. Active Alerts -->
        <section class="bridge-section" v-if="alerts.length">
          <div class="section-header">
            <span class="section-label text-warning">ACTIVE ALERTS</span>
          </div>
          <div class="alert-list">
            <div
              v-for="(alert, i) in alerts"
              :key="i"
              class="alert-item"
              :style="{ borderLeftColor: severityColor(alert.severity) }"
            >
              <div class="alert-header">
                <span
                  class="alert-severity"
                  :style="{ color: severityColor(alert.severity) }"
                >
                  {{ alert.severity }}
                </span>
                <span class="alert-title">{{ alert.title }}</span>
              </div>
              <div class="alert-desc text-dim">{{ alert.description }}</div>
            </div>
          </div>
        </section>

        <!-- 7. Recommended Actions -->
        <section class="bridge-section" v-if="recommendations.length">
          <div class="section-header">
            <span class="section-label text-secondary">RECOMMENDED ACTIONS</span>
          </div>
          <RecommendationPanel :recommendations="recommendations" />
        </section>
      </div>

      <!-- Right column -->
      <div class="bridge-col">

        <!-- 5. Current Location -->
        <section class="bridge-section" v-if="location && location.system">
          <div class="section-header">
            <span class="section-label">CURRENT LOCATION</span>
          </div>
          <div class="location-info">
            <div class="location-system">{{ location.system }}</div>
            <div v-if="location.body" class="location-body text-dim">
              {{ location.body }}
            </div>
            <div class="location-grid">
              <div v-if="location.security" class="loc-item">
                <span class="loc-label">SECURITY</span>
                <span class="loc-value">{{ location.security }}</span>
              </div>
              <div v-if="location.economy" class="loc-item">
                <span class="loc-label">ECONOMY</span>
                <span class="loc-value">{{ location.economy }}</span>
              </div>
              <div v-if="location.population" class="loc-item">
                <span class="loc-label">POPULATION</span>
                <span class="loc-value">{{ location.population.toLocaleString() }}</span>
              </div>
              <div v-if="location.faction" class="loc-item">
                <span class="loc-label">FACTION</span>
                <span class="loc-value">{{ location.faction }}</span>
              </div>
            </div>
            <div v-if="location.stations.length" class="location-stations text-dim">
              Stations: {{ location.stations.join(', ') }}
            </div>
          </div>
        </section>

        <!-- 8. Expedition Summary -->
        <section class="bridge-section" v-if="expedition">
          <div class="section-header">
            <span class="section-label">EXPEDITION SUMMARY</span>
          </div>
          <div class="expedition-grid">
            <div class="exp-item">
              <span class="exp-value">{{ expedition.jumps }}</span>
              <span class="exp-label">JUMPS</span>
            </div>
            <div class="exp-item">
              <span class="exp-value">{{ expedition.distance_ly.toFixed(1) }}</span>
              <span class="exp-label">LY</span>
            </div>
            <div class="exp-item">
              <span class="exp-value">{{ expedition.bodies_scanned }}</span>
              <span class="exp-label">SCANNED</span>
            </div>
            <div class="exp-item">
              <span class="exp-value">{{ expedition.organic_scans }}</span>
              <span class="exp-label">SAMPLES</span>
            </div>
            <div class="exp-item">
              <span class="exp-value">{{ expedition.missions_completed }}</span>
              <span class="exp-label">MISSIONS</span>
            </div>
          </div>
        </section>

        <!-- 4. Department Status -->
        <section class="bridge-section">
          <div class="section-header">
            <span class="section-label">DEPARTMENT STATUS</span>
          </div>
          <div class="dept-grid">
            <div
              v-for="dept in departments"
              :key="dept.department"
              class="dept-item"
            >
              <div class="dept-header">
                <span class="dept-code">{{ deptName(dept.department) }}</span>
                <span
                  class="dept-status"
                  :style="{ color: deptStatusColor(dept.status) }"
                >
                  {{ dept.status }}
                </span>
              </div>
            </div>
          </div>
        </section>

        <!-- 9. Captain's Log -->
        <section class="bridge-section" v-if="log.length">
          <div class="section-header">
            <span class="section-label">CAPTAIN'S LOG</span>
          </div>
          <div class="log-list">
            <div v-for="(entry, i) in log" :key="i" class="log-item">
              <span class="log-dept text-muted">{{ deptName(entry.department) }}</span>
              <span class="log-event">{{ entry.event }}</span>
            </div>
          </div>
        </section>
      </div>
    </div>
  </div>

  <div v-else class="loading text-muted">
    Connecting to ship computer...
  </div>
</template>

<style scoped>
.bridge-page {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
  max-width: 1200px;
  margin: 0 auto;
}

.bridge-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--spacing-md);
}

.bridge-col {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.bridge-section {
  background: var(--color-panel);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: var(--spacing-md);
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--spacing-sm);
}

.section-label {
  font-size: var(--font-size-xs);
  text-transform: uppercase;
  letter-spacing: 2px;
  color: var(--color-primary);
  font-weight: 700;
}

/* Briefing */
.briefing-section {
  border-color: var(--color-border-active);
}

.briefing-text {
  font-size: var(--font-size-md);
  line-height: 1.6;
  color: var(--color-text);
}

/* Ship Status */
.ship-name-line {
  display: flex;
  align-items: baseline;
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-md);
}

.ship-type {
  font-size: var(--font-size-lg);
  font-weight: 700;
  color: var(--color-primary);
}

.ship-name {
  font-size: var(--font-size-sm);
}

.ship-metrics {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.metric {
  display: grid;
  grid-template-columns: 50px 1fr 60px;
  align-items: center;
  gap: var(--spacing-sm);
}

.metric-label {
  font-size: var(--font-size-xs);
  color: var(--color-text-muted);
  letter-spacing: 1px;
}

.metric-bar {
  height: 6px;
  background: var(--color-background);
  border-radius: 3px;
  overflow: hidden;
}

.metric-fill {
  height: 100%;
  border-radius: 3px;
  transition: width var(--animation-normal);
}

.metric-value {
  font-size: var(--font-size-xs);
  text-align: right;
  font-weight: 600;
}

.ship-meta {
  margin-top: var(--spacing-sm);
  font-size: var(--font-size-xs);
}

/* Mission */
.mission-title {
  font-size: var(--font-size-md);
  font-weight: 700;
  color: var(--color-primary);
  margin-bottom: var(--spacing-xs);
}

.mission-details {
  display: flex;
  justify-content: space-between;
  font-size: var(--font-size-sm);
  margin-bottom: var(--spacing-xs);
}

.mission-expiry {
  font-size: var(--font-size-xs);
}

/* Alerts */
.alert-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
}

.alert-item {
  border-left: 3px solid;
  padding-left: var(--spacing-sm);
}

.alert-header {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  margin-bottom: 2px;
}

.alert-severity {
  font-size: var(--font-size-xs);
  font-weight: 700;
  letter-spacing: 1px;
}

.alert-title {
  font-size: var(--font-size-sm);
  font-weight: 600;
}

.alert-desc {
  font-size: var(--font-size-xs);
}

/* Location */
.location-system {
  font-size: var(--font-size-xl);
  font-weight: 700;
  color: var(--color-primary);
}

.location-body {
  font-size: var(--font-size-sm);
  margin-bottom: var(--spacing-sm);
}

.location-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--spacing-xs);
  margin-bottom: var(--spacing-sm);
}

.loc-item {
  display: flex;
  flex-direction: column;
}

.loc-label {
  font-size: 10px;
  color: var(--color-text-muted);
  letter-spacing: 1px;
  text-transform: uppercase;
}

.loc-value {
  font-size: var(--font-size-sm);
}

.location-stations {
  font-size: var(--font-size-xs);
  border-top: 1px solid var(--color-border);
  padding-top: var(--spacing-xs);
}

/* Expedition */
.expedition-grid {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: var(--spacing-xs);
}

.exp-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
}

.exp-value {
  font-size: var(--font-size-lg);
  font-weight: 700;
  color: var(--color-primary);
}

.exp-label {
  font-size: 10px;
  color: var(--color-text-muted);
  letter-spacing: 1px;
}

/* Departments */
.dept-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--spacing-xs);
}

.dept-item {
  background: var(--color-background);
  border-radius: var(--radius-sm);
  padding: var(--spacing-sm);
}

.dept-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.dept-code {
  font-size: var(--font-size-xs);
  font-weight: 700;
  letter-spacing: 1px;
}

.dept-status {
  font-size: var(--font-size-xs);
  font-weight: 700;
}

/* Captain's Log */
.log-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
}

.log-item {
  display: flex;
  gap: var(--spacing-sm);
  font-size: var(--font-size-xs);
  padding: var(--spacing-xs) 0;
  border-bottom: 1px solid var(--color-border);
}

.log-item:last-child {
  border-bottom: none;
}

.log-dept {
  font-weight: 700;
  letter-spacing: 1px;
  min-width: 30px;
}

.log-event {
  color: var(--color-text-dim);
}

/* Loading */
.loading {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 200px;
  font-size: var(--font-size-md);
}

/* Responsive */
@media (max-width: 900px) {
  .bridge-grid {
    grid-template-columns: 1fr;
  }
  .dept-grid {
    grid-template-columns: repeat(3, 1fr);
  }
}
</style>
