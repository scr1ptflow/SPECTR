<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useBridgeStore } from '@/stores/bridge'
import DepartmentHeader from '@/components/DepartmentHeader.vue'
import StatusCard from '@/components/StatusCard.vue'

const bridge = useBridgeStore()

onMounted(() => {
  bridge.fetchState()
})

const ship = computed(() => bridge.report?.ship_status)
</script>

<template>
  <div>
    <DepartmentHeader title="SHIP" subtitle="Vessel Status & Modules" />

    <div v-if="ship" class="ship-grid">
      <StatusCard label="Ship Type" :value="ship.ship_type || '---'" />
      <StatusCard label="Name" :value="ship.ship_name || '---'" />
      <StatusCard label="Ident" :value="ship.ship_ident || '---'" />
      <StatusCard label="Hull" :value="`${ship.hull_health.toFixed(0)}%`"
        :color="ship.hull_health < 50 ? 'var(--color-danger)' : 'var(--color-success)'" />
      <StatusCard label="Rebuy" :value="`${ship.rebuy.toLocaleString()} CR`" />
      <StatusCard label="Cargo" :value="`${ship.cargo_count}/${ship.cargo_capacity}`" />
    </div>

    <div v-else class="loading text-muted">No ship data</div>
  </div>
</template>

<style scoped>
.ship-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-lg);
}
.section-title {
  font-size: var(--font-size-xs);
  color: var(--color-text-muted);
  text-transform: uppercase;
  letter-spacing: 1px;
  margin-bottom: var(--spacing-sm);
}
.module-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: var(--spacing-xs);
}
.module-card {
  background: var(--color-panel);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  padding: var(--spacing-sm);
  display: flex;
  flex-direction: column;
}
.module-slot {
  font-size: var(--font-size-xs);
}
.module-name {
  font-size: var(--font-size-sm);
  font-weight: 600;
}
.loading {
  display: flex;
  justify-content: center;
  padding: var(--spacing-xl);
}
</style>
