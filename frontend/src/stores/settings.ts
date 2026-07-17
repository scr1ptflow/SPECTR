import { defineStore } from 'pinia'
import { ref } from 'vue'
import { settingsApi, type AppSettings } from '@/api/endpoints'

export const useSettingsStore = defineStore('settings', () => {
  const settings = ref<AppSettings | null>(null)
  const saving = ref(false)

  async function fetchSettings() {
    settings.value = await settingsApi.get()
  }

  async function updateSettings(data: Partial<AppSettings>) {
    saving.value = true
    try {
      settings.value = await settingsApi.update(data)
    } finally {
      saving.value = false
    }
  }

  return { settings, saving, fetchSettings, updateSettings }
})
