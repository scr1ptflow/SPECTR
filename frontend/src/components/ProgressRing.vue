<script setup lang="ts">
defineProps<{
  label: string
  value: number
  max?: number
  color?: string
}>()

const maxVal = (props: { max?: number }) => props.max || 100
</script>

<template>
  <div class="progress-ring">
    <svg viewBox="0 0 36 36" class="ring-svg">
      <path
        class="ring-bg"
        d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
      />
      <path
        class="ring-fill"
        :stroke="color || 'var(--color-primary)'"
        :stroke-dasharray="`${(value / (max || 100)) * 100}, 100`"
        d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
      />
    </svg>
    <div class="ring-label">
      <span class="ring-value">{{ value }}%</span>
    </div>
    <div class="ring-text text-muted">{{ label }}</div>
  </div>
</template>

<style scoped>
.progress-ring {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--spacing-xs);
}
.ring-svg {
  width: 64px;
  height: 64px;
}
.ring-bg {
  fill: none;
  stroke: var(--color-border);
  stroke-width: 3;
}
.ring-fill {
  fill: none;
  stroke-width: 3;
  stroke-linecap: round;
  transition: stroke-dasharray var(--animation-normal);
}
.ring-label {
  position: relative;
  margin-top: -44px;
  margin-bottom: 24px;
}
.ring-value {
  font-size: var(--font-size-sm);
  font-weight: 700;
}
.ring-text {
  font-size: var(--font-size-xs);
}
</style>
