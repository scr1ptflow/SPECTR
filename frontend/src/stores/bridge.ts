import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { bridgeApi, type BridgeReport } from '@/api/endpoints'

export const useBridgeStore = defineStore('bridge', () => {
  const report = ref<BridgeReport | null>(null)
  const connected = ref(false)
  const lastUpdate = ref<string>('')

  const isLoaded = computed(() => report.value !== null)

  async function fetchState() {
    try {
      report.value = await bridgeApi.get()
      lastUpdate.value = report.value.generated
      connected.value = true
    } catch {
      connected.value = false
    }
  }

  function updateFromWebSocket(data: any) {
    if (data.type === 'state.updated') {
      lastUpdate.value = data.timestamp
      fetchState()
    } else if (data.type === 'state.full') {
      fetchState()
    }
  }

  return { report, connected, lastUpdate, isLoaded, fetchState, updateFromWebSocket }
})
