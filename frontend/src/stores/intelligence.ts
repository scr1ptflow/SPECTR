import { defineStore } from 'pinia'
import { ref } from 'vue'
import { intelligenceApi, type IntelligenceReport } from '@/api/endpoints'

export const useIntelligenceStore = defineStore('intelligence', () => {
  const intelligence = ref<IntelligenceReport | null>(null)

  async function fetch() {
    intelligence.value = await intelligenceApi.get()
  }

  return { intelligence, fetch }
})
