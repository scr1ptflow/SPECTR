<script setup lang="ts">
import { useBridgeStore } from '@/stores/bridge'
import { onMounted, onUnmounted } from 'vue'
import { api } from '@/api/client'

const bridge = useBridgeStore()

let unsubscribe: (() => void) | null = null

onMounted(() => {
  api.connectWebSocket()
  unsubscribe = api.onStateUpdate((data) => bridge.updateFromWebSocket(data))
})

onUnmounted(() => {
  unsubscribe?.()
})
</script>

<template>
  <router-view />
</template>
