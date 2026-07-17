<script setup lang="ts">
import { onMounted, ref, computed } from 'vue'
import { useSettingsStore } from '@/stores/settings'
import DepartmentHeader from '@/components/DepartmentHeader.vue'

const store = useSettingsStore()

const journalPath = ref('')
const inaraKey = ref('')
const edsmKey = ref('')
const saved = ref(false)

onMounted(async () => {
  await store.fetchSettings()
  if (store.settings) {
    journalPath.value = store.settings.journal_path
    inaraKey.value = store.settings.inara_api_key
    edsmKey.value = store.settings.edsm_api_key
  }
})

const hasChanges = computed(() => {
  if (!store.settings) return false
  return (
    journalPath.value !== store.settings.journal_path ||
    inaraKey.value !== store.settings.inara_api_key ||
    edsmKey.value !== store.settings.edsm_api_key
  )
})

async function save() {
  await store.updateSettings({
    journal_path: journalPath.value,
    inara_api_key: inaraKey.value,
    edsm_api_key: edsmKey.value,
  })
  saved.value = true
  setTimeout(() => { saved.value = false }, 2000)
}
</script>

<template>
  <div>
    <DepartmentHeader
      title="Settings"
      subtitle="Configure Elite Bridge connections and paths"
    />

    <div class="settings-content">
      <!-- Connections -->
      <div class="settings-section">
        <h3 class="section-title">CONNECTIONS</h3>

        <div class="field">
          <label class="field-label">Journal Path</label>
          <div class="field-hint text-dim">Path to your Elite Dangerous journal directory</div>
          <input
            v-model="journalPath"
            type="text"
            class="field-input"
            placeholder="C:\Users\...\Saved Games\Frontier Developments\Elite Dangerous\options\logs"
          />
        </div>

        <div class="field">
          <label class="field-label">Inara API Key</label>
          <div class="field-hint text-dim">Personal API key from inara.cz</div>
          <input
            v-model="inaraKey"
            type="password"
            class="field-input"
            placeholder="Enter your Inara API key"
          />
        </div>

        <div class="field">
          <label class="field-label">EDSM API Key</label>
          <div class="field-hint text-dim">Personal API key from edsm.net</div>
          <input
            v-model="edsmKey"
            type="password"
            class="field-input"
            placeholder="Enter your EDSM API key"
          />
        </div>
      </div>

      <!-- Save -->
      <div class="settings-actions">
        <button
          class="save-btn"
          :disabled="!hasChanges || store.saving"
          @click="save"
        >
          {{ store.saving ? 'SAVING...' : saved ? 'SAVED' : 'SAVE SETTINGS' }}
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.settings-content {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xl);
}

.settings-section {
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

.field {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
}

.field-label {
  font-size: var(--font-size-sm);
  font-weight: 600;
  color: var(--color-text);
}

.field-hint {
  font-size: var(--font-size-xs);
}

.field-input {
  background: var(--color-panel);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  padding: 10px var(--spacing-md);
  color: var(--color-text);
  font-family: var(--font-mono);
  font-size: var(--font-size-sm);
  outline: none;
  transition: border-color var(--animation-fast);
}

.field-input:focus {
  border-color: var(--color-primary);
}

.field-input::placeholder {
  color: var(--color-text-muted);
}

.settings-actions {
  display: flex;
  justify-content: flex-end;
}

.save-btn {
  background: rgba(245, 166, 35, 0.15);
  border: 1px solid var(--color-primary);
  color: var(--color-primary);
  padding: 10px var(--spacing-lg);
  border-radius: var(--radius-sm);
  font-family: var(--font-mono);
  font-size: var(--font-size-xs);
  font-weight: 600;
  letter-spacing: 1px;
  cursor: pointer;
  transition: all var(--animation-fast);
}

.save-btn:hover:not(:disabled) {
  background: rgba(245, 166, 35, 0.25);
}

.save-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}
</style>
