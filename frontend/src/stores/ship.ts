import { defineStore } from 'pinia'
import { ref } from 'vue'
import { shipApi, type ShipState } from '@/api/endpoints'

export const useShipStore = defineStore('ship', () => {
  const ship = ref<ShipState | null>(null)

  async function fetch() {
    ship.value = await shipApi.get()
  }

  return { ship, fetch }
})
