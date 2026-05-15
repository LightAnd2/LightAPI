import { useEffect, useRef, useCallback } from 'react'

const WS_BASE = import.meta.env.VITE_WS_URL || (
  typeof window !== 'undefined'
    ? (window.location.protocol === 'https:' ? 'wss' : 'ws') + '://' + window.location.host
    : ''
)

export function useWebSocket(path, onMessage) {
  const wsRef = useRef(null)
  const onMessageRef = useRef(onMessage)
  onMessageRef.current = onMessage

  const reconnect = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.onclose = null
      wsRef.current.close()
    }
    const ws = new WebSocket(`${WS_BASE}${path}`)
    wsRef.current = ws

    ws.onmessage = (e) => {
      try {
        const data = JSON.parse(e.data)
        onMessageRef.current(data)
      } catch {}
    }

    ws.onclose = () => {
      setTimeout(reconnect, 3000)
    }

    ws.onerror = () => {
      ws.close()
    }
  }, [path])

  useEffect(() => {
    reconnect()
    return () => {
      if (wsRef.current) {
        wsRef.current.onclose = null
        wsRef.current.close()
      }
    }
  }, [reconnect])
}
