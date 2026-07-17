import { defineStore } from 'pinia'
import { ref } from 'vue'
import { missionsApi, type OperationsReport } from '@/api/endpoints'

export const useMissionStore = defineStore('missions', () => {
  const missions = ref<OperationsReport | null>(null)

  async function fetch() {
    missions.value = await missionsApi.get()
  }

  return { missions, fetch }
})
