import { defineStore } from 'pinia'
import { ref } from 'vue'
import { archiveApi, type ArchiveReport } from '@/api/endpoints'

export const useArchiveStore = defineStore('archive', () => {
  const archive = ref<ArchiveReport | null>(null)

  async function fetch() {
    archive.value = await archiveApi.get()
  }

  return { archive, fetch }
})
