import { defineStore } from 'pinia'
import { ref } from 'vue'
import { commanderApi, type CommanderReport } from '@/api/endpoints'

export const useCommanderStore = defineStore('commander', () => {
  const report = ref<CommanderReport | null>(null)

  async function fetch() {
    report.value = await commanderApi.get()
  }

  return { report, fetch }
})
