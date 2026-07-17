import { defineStore } from 'pinia'
import { ref } from 'vue'
import { scansApi, type LaboratoryReport } from '@/api/endpoints'

export const useScanStore = defineStore('scans', () => {
  const scans = ref<LaboratoryReport | null>(null)

  async function fetch() {
    scans.value = await scansApi.get()
  }

  return { scans, fetch }
})
