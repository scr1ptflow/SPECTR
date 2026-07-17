import { defineStore } from 'pinia'
import { ref } from 'vue'
import { sessionApi, type SessionState } from '@/api/endpoints'

export const useSessionStore = defineStore('session', () => {
  const session = ref<SessionState | null>(null)

  async function fetch() {
    session.value = await sessionApi.get()
  }

  return { session, fetch }
})
