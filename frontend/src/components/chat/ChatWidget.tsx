import { MessageSquare, X } from "lucide-react"
import { useEffect, useRef } from "react"

import { ChatComposer } from "@/components/chat/ChatComposer"
import { ChatMessage } from "@/components/chat/ChatMessage"
import { ConfirmationCard } from "@/components/chat/ConfirmationCard"
import { useChatSocket } from "@/hooks/useChatSocket"
import { cn } from "@/lib/utils"
import { useChatStore } from "@/stores/chatStore"

export function ChatWidget() {
  const {
    isOpen,
    messages,
    pending,
    typing,
    connected,
    unreadCount,
    toggle,
    setPending,
  } = useChatStore()
  const { send } = useChatSocket()
  const scrollRef = useRef<HTMLDivElement>(null)

  // Auto-scroll à chaque nouveau message
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [messages, typing, isOpen, pending])

  const handleConfirm = () => {
    if (!pending) return
    send({ type: "confirm_action", action_id: pending.actionId, accept: true })
    setPending(null)
  }
  const handleCancel = () => {
    if (!pending) return
    send({ type: "confirm_action", action_id: pending.actionId, accept: false })
    setPending(null)
  }

  return (
    <>
      {/* Bouton flottant */}
      <button
        type="button"
        onClick={toggle}
        className={cn(
          "fixed bottom-6 right-6 z-50 flex h-14 w-14 items-center justify-center rounded-full",
          "bg-accent text-bg-main shadow-glow-strong",
          "hover:bg-accent-bright transition-colors",
        )}
        aria-label={isOpen ? "Fermer le chat" : "Ouvrir le chat"}
      >
        {isOpen ? <X className="h-6 w-6" /> : <MessageSquare className="h-6 w-6" />}
        {!isOpen && unreadCount > 0 && (
          <span className="absolute -top-1 -right-1 flex h-5 w-5 items-center justify-center rounded-full bg-danger text-[10px] font-bold text-white">
            {unreadCount > 9 ? "9+" : unreadCount}
          </span>
        )}
      </button>

      {/* Panneau */}
      <div
        className={cn(
          "fixed bottom-24 right-6 z-50 flex h-[560px] w-[400px] max-w-[calc(100vw-3rem)] flex-col",
          "rounded-card border border-border bg-bg-card/95 backdrop-blur-2xl shadow-glow",
          "transition-all duration-300",
          isOpen
            ? "opacity-100 translate-y-0 pointer-events-auto"
            : "opacity-0 translate-y-4 pointer-events-none",
        )}
      >
        {/* Header */}
        <header className="flex items-center justify-between border-b border-border px-4 py-3">
          <div className="flex items-center gap-2">
            <span
              className={cn(
                "h-2 w-2 rounded-full",
                connected ? "bg-accent animate-pulse-glow" : "bg-text-dim",
              )}
            />
            <span className="font-mono text-xs uppercase tracking-wider text-text-secondary">
              Assistant MAC
            </span>
          </div>
          <button
            type="button"
            onClick={toggle}
            className="text-text-dim hover:text-text-primary"
            aria-label="Fermer"
          >
            <X className="h-4 w-4" />
          </button>
        </header>

        {/* Transcript */}
        <div
          ref={scrollRef}
          className="flex-1 space-y-3 overflow-y-auto px-4 py-4"
        >
          {messages.length === 0 && (
            <p className="text-center text-xs text-text-dim font-mono">
              [ no messages — say hi or type /help ]
            </p>
          )}
          {messages.map((m) => (
            <ChatMessage key={m.id} message={m} />
          ))}
          {typing && (
            <div className="flex items-center gap-2 px-2 text-xs text-text-dim">
              <span className="font-mono">typing</span>
              <span className="flex gap-1">
                <span className="h-1 w-1 animate-pulse-glow rounded-full bg-text-dim" />
                <span className="h-1 w-1 animate-pulse-glow rounded-full bg-text-dim" style={{ animationDelay: "150ms" }} />
                <span className="h-1 w-1 animate-pulse-glow rounded-full bg-text-dim" style={{ animationDelay: "300ms" }} />
              </span>
            </div>
          )}
          {pending && (
            <ConfirmationCard
              pending={pending}
              onConfirm={handleConfirm}
              onCancel={handleCancel}
            />
          )}
        </div>

        {/* Composer */}
        <ChatComposer onSend={(c) => send({ type: "message", content: c })} disabled={!connected} />
      </div>
    </>
  )
}
