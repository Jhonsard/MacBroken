import { Send } from "lucide-react"
import { type FormEvent, useState } from "react"

import { Button } from "@/components/ui/button"

interface Props {
  onSend: (content: string) => void
  disabled?: boolean
}

export function ChatComposer({ onSend, disabled }: Props) {
  const [value, setValue] = useState("")

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault()
    const v = value.trim()
    if (!v) return
    onSend(v)
    setValue("")
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="flex items-end gap-2 border-t border-border p-3 bg-bg-card/40"
    >
      <textarea
        rows={1}
        value={value}
        disabled={disabled}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault()
            handleSubmit(e as unknown as FormEvent)
          }
        }}
        placeholder="Tapez /help…"
        className="flex-1 resize-none rounded-md border border-border bg-bg-input px-3 py-2 text-sm text-text-primary placeholder:text-text-dim focus:border-accent focus:outline-none max-h-32"
      />
      <Button type="submit" size="icon" disabled={disabled || !value.trim()}>
        <Send className="h-4 w-4" />
      </Button>
    </form>
  )
}
