import { defineStore } from 'pinia'
import { ref } from 'vue'
import { navigationApi, type NavigationReport } from '@/api/endpoints'

export const useNavigationStore = defineStore('navigation', () => {
  const report = ref<NavigationReport | null>(null)

  async function fetch() {
    report.value = await navigationApi.get()
  }

  return { report, fetch }
})
