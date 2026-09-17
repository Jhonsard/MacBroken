import { useCallback, useEffect, useRef } from "react"

import { useAuthStore } from "@/stores/authStore"
import { useChatStore } from "@/stores/chatStore"
import type { ClientFrame, ServerFrame } from "@/types/chat"

const WS_BASE =
  (import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api/v1")
    .replace(/^http/, "ws")

export function useChatSocket() {
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimer = useRef<number | null>(null)
  const attemptRef = useRef(0)
  const closedByUser = useRef(false)

  const accessToken = useAuthStore((s) => s.accessToken)
  const {
    addMessage,
    setHistory,
    setPending,
    setTyping,
    setConnected,
  } = useChatStore.getState()

  const connect = useCallback(() => {
    if (!accessToken) return
    if (wsRef.current?.readyState === WebSocket.OPEN) return

    const url = `${WS_BASE}/ws/chat?token=${encodeURIComponent(accessToken)}`
    const ws = new WebSocket(url)
    wsRef.current = ws

    ws.onopen = () => {
      attemptRef.current = 0
      setConnected(true)
    }

    ws.onmessage = (evt) => {
      let frame: ServerFrame
      try {
        frame = JSON.parse(evt.data)
      } catch {
        return
      }

      switch (frame.type) {
        case "message":
          addMessage({
            id: frame.id ?? crypto.randomUUID(),
            role: frame.role,
            content: frame.content,
            timestamp: frame.timestamp ?? new Date().toISOString(),
          })
          break
        case "typing":
          setTyping(frame.state === "on")
          break
        case "action_request":
          setPending({
            actionId: frame.action_id,
            action: frame.action,
            params: frame.params,
            summary: frame.summary,
          })
          break
        case "action_result": {
          const text = frame.success
            ? ((frame.data?.text as string) ?? "Action exécutée.")
            : `⚠️ ${frame.error ?? "Échec de l'action."}`
          addMessage({
            id: crypto.randomUUID(),
            role: "bot",
            content: text,
            timestamp: new Date().toISOString(),
          })
          setPending(null)
          break
        }
        case "history":
          setHistory(
            frame.messages.map((m) => ({
              id: crypto.randomUUID(),
              role: m.role,
              content: m.content,
              timestamp: m.timestamp,
            })),
          )
          break
        case "error":
          addMessage({
            id: crypto.randomUUID(),
            role: "system",
            content: `⚠️ ${frame.message}`,
            timestamp: new Date().toISOString(),
          })
          break
      }
    }

    ws.onclose = (evt) => {
      setConnected(false)
      wsRef.current = null
      if (closedByUser.current) return
      if (evt.code === 4401 || evt.code === 4403) return // auth fail → pas de retry
      // Reconnexion exponentielle
      attemptRef.current += 1
      const delay = Math.min(30_000, 1000 * 2 ** Math.min(attemptRef.current, 5))
      reconnectTimer.current = window.setTimeout(() => connect(), delay)
    }

    ws.onerror = () => {
      // onclose gère la reconnexion
    }
  }, [accessToken, addMessage, setHistory, setPending, setTyping, setConnected])

  const disconnect = useCallback(() => {
    closedByUser.current = true
    if (reconnectTimer.current) {
      clearTimeout(reconnectTimer.current)
      reconnectTimer.current = null
    }
    wsRef.current?.close()
    wsRef.current = null
  }, [])

  const send = useCallback((frame: ClientFrame) => {
    const ws = wsRef.current
    if (!ws || ws.readyState !== WebSocket.OPEN) return false
    ws.send(JSON.stringify(frame))
    return true
  }, [])

  useEffect(() => {
    if (accessToken) {
      closedByUser.current = false
      connect()
    } else {
      disconnect()
    }
    return () => {
      disconnect()
    }
  }, [accessToken, connect, disconnect])

  return { send, connect, disconnect }
}
