export type ChatRole = "user" | "bot" | "system"

export interface ChatMessage {
  id: string
  role: ChatRole
  content: string
  timestamp: string
}

export interface PendingAction {
  actionId: string
  action: string
  params: Record<string, unknown>
  summary: string
}

// --- Frames serveur ---
export type ServerFrame =
  | { type: "message"; id: string; role: ChatRole; content: string; timestamp: string | null }
  | { type: "typing"; state: "on" | "off" }
  | { type: "action_request"; action_id: string; action: string; params: Record<string, unknown>; summary: string; requires_confirmation: boolean }
  | { type: "action_result"; action_id: string; success: boolean; data?: Record<string, unknown>; error?: string }
  | { type: "history"; messages: Array<{ role: ChatRole; content: string; timestamp: string }> }
  | { type: "error"; message: string }

// --- Frames client ---
export type ClientFrame =
  | { type: "message"; content: string }
  | { type: "confirm_action"; action_id: string; accept: boolean }
