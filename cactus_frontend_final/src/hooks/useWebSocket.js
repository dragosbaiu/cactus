import { useEffect, useRef, useCallback } from 'react'
import { useGameStore } from '../store/gameStore'

const WS_BASE = import.meta.env.VITE_WS_URL || 'ws://localhost:8000'
const RECONNECT_DELAY_MS = 2000

export function useWebSocket(roomCode, token) {
  const wsRef = useRef(null)
  const reconnectTimer = useRef(null)
  const { handleServerMessage, setConnectionStatus } = useGameStore()

  const connect = useCallback(() => {
    if (!roomCode || !token) return
    if (wsRef.current?.readyState === WebSocket.OPEN) return

    const url = `${WS_BASE}/rooms/${roomCode}/ws?token=${token}`
    const ws = new WebSocket(url)
    wsRef.current = ws

    ws.onopen = () => {
      setConnectionStatus('connected')
      if (reconnectTimer.current) {
        clearTimeout(reconnectTimer.current)
        reconnectTimer.current = null
      }
    }

    ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data)
        handleServerMessage(message)
      } catch (e) {
        console.error('Failed to parse server message:', e)
      }
    }

    ws.onclose = (event) => {
      setConnectionStatus('disconnected')
      // Don't reconnect on fatal errors (bad token, room not found)
      if (event.code !== 4001 && event.code !== 4004) {
        reconnectTimer.current = setTimeout(connect, RECONNECT_DELAY_MS)
      }
    }

    ws.onerror = () => {
      setConnectionStatus('error')
    }
  }, [roomCode, token, handleServerMessage, setConnectionStatus])

  const sendAction = useCallback((action, data = {}) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ action, ...data }))
    } else {
      console.warn('WebSocket not open, cannot send:', action)
    }
  }, [])

  useEffect(() => {
    connect()
    return () => {
      if (reconnectTimer.current) clearTimeout(reconnectTimer.current)
      if (wsRef.current) {
        wsRef.current.onclose = null
        wsRef.current.close()
      }
    }
  }, [connect])

  return { sendAction }
}
