import { Check, X } from "lucide-react"

import { Button } from "@/components/ui/button"
import type { PendingAction } from "@/types/chat"

interface Props {
  pending: PendingAction
  onConfirm: () => void
  onCancel: () => void
}

export function ConfirmationCard({ pending, onConfirm, onCancel }: Props) {
  return (
    <div className="rounded-lg border border-info/40 bg-info/5 p-3 space-y-3 animate-msg-in">
      <div className="flex items-center gap-2">
        <span className="text-[10px] font-mono uppercase tracking-wider text-info">
          Action proposée
        </span>
      </div>
      <p className="text-sm text-text-primary">{pending.summary}</p>
      <div className="flex gap-2">
        <Button size="sm" onClick={onConfirm} className="flex-1">
          <Check className="mr-1 h-3 w-3" />
          Confirmer
        </Button>
        <Button
          size="sm"
          variant="outline"
          onClick={onCancel}
          className="flex-1"
        >
          <X className="mr-1 h-3 w-3" />
          Annuler
        </Button>
      </div>
    </div>
  )
}
