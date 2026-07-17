const API_BASE = '/api/v1'

class ApiClient {
  private baseUrl: string
  private ws: WebSocket | null = null
  private wsListeners: Map<string, ((data: any) => void)[]> = new Map()

  constructor(baseUrl: string = API_BASE) {
    this.baseUrl = baseUrl
  }

  async get<T>(path: string): Promise<T> {
    const response = await fetch(`${this.baseUrl}${path}`)
    if (!response.ok) {
      throw new Error(`API error: ${response.status} ${response.statusText}`)
    }
    return response.json()
  }

  async put<T>(path: string, data: unknown): Promise<T> {
    const response = await fetch(`${this.baseUrl}${path}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    })
    if (!response.ok) {
      throw new Error(`API error: ${response.status} ${response.statusText}`)
    }
    return response.json()
  }

  connectWebSocket(): void {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const wsUrl = `${protocol}//${window.location.host}/ws`
    this.ws = new WebSocket(wsUrl)

    this.ws.onmessage = (event) => {
      const data = JSON.parse(event.data)
      const listeners = this.wsListeners.get(data.type) || []
      listeners.forEach((fn) => fn(data))
    }

    this.ws.onclose = () => {
      setTimeout(() => this.connectWebSocket(), 3000)
    }
  }

  onStateUpdate(callback: (data: any) => void): () => void {
    if (!this.wsListeners.has('state.updated')) {
      this.wsListeners.set('state.updated', [])
    }
    this.wsListeners.get('state.updated')!.push(callback)
    return () => {
      const listeners = this.wsListeners.get('state.updated') || []
      const idx = listeners.indexOf(callback)
      if (idx >= 0) listeners.splice(idx, 1)
    }
  }

  onFullState(callback: (data: any) => void): () => void {
    if (!this.wsListeners.has('state.full')) {
      this.wsListeners.set('state.full', [])
    }
    this.wsListeners.get('state.full')!.push(callback)
    return () => {
      const listeners = this.wsListeners.get('state.full') || []
      const idx = listeners.indexOf(callback)
      if (idx >= 0) listeners.splice(idx, 1)
    }
  }

  requestRefresh(): void {
    this.ws?.send('refresh')
  }
}

export const api = new ApiClient()
