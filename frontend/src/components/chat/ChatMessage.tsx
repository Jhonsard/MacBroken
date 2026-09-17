import { cn } from "@/lib/utils"
import type { ChatMessage as TMsg } from "@/types/chat"

interface Props {
  message: TMsg
}

export function ChatMessage({ message }: Props) {
  const isUser = message.role === "user"
  const isSystem = message.role === "system"

  return (
    <div
      className={cn(
        "flex w-full animate-msg-in",
        isUser ? "justify-end" : "justify-start",
      )}
    >
      <div
        className={cn(
          "max-w-[85%] rounded-lg px-3 py-2 text-sm whitespace-pre-wrap break-words",
          isUser && "bg-accent/15 text-text-primary border border-accent/30",
          !isUser && !isSystem && "bg-bg-card/70 border border-border text-text-primary",
          isSystem && "bg-warning/10 border border-warning/30 text-warning text-xs",
        )}
      >
        {message.content}
      </div>
    </div>
  )
}
