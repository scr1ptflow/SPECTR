import { defineStore } from 'pinia'
import { ref } from 'vue'
import { engineeringApi, type EngineeringReport } from '@/api/endpoints'

export const useEngineeringStore = defineStore('engineering', () => {
  const report = ref<EngineeringReport | null>(null)

  async function fetch() {
    report.value = await engineeringApi.get()
  }

  return { report, fetch }
})
