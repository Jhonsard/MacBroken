import { create } from "zustand"

import type { ChatMessage, PendingAction } from "@/types/chat"

interface ChatState {
  isOpen: boolean
  messages: ChatMessage[]
  pending: PendingAction | null
  typing: boolean
  connected: boolean
  unreadCount: number

  toggle: () => void
  open: () => void
  close: () => void
  addMessage: (m: ChatMessage) => void
  setHistory: (msgs: ChatMessage[]) => void
  setPending: (p: PendingAction | null) => void
  setTyping: (t: boolean) => void
  setConnected: (c: boolean) => void
  resetUnread: () => void
  clear: () => void
}

export const useChatStore = create<ChatState>((set) => ({
  isOpen: false,
  messages: [],
  pending: null,
  typing: false,
  connected: false,
  unreadCount: 0,

  toggle: () => set((s) => ({ isOpen: !s.isOpen, unreadCount: s.isOpen ? s.unreadCount : 0 })),
  open: () => set({ isOpen: true, unreadCount: 0 }),
  close: () => set({ isOpen: false }),
  addMessage: (m) =>
    set((s) => ({
      messages: [...s.messages, m],
      unreadCount: s.isOpen ? 0 : s.unreadCount + (m.role === "bot" ? 1 : 0),
    })),
  setHistory: (msgs) => set({ messages: msgs }),
  setPending: (p) => set({ pending: p }),
  setTyping: (t) => set({ typing: t }),
  setConnected: (c) => set({ connected: c }),
  resetUnread: () => set({ unreadCount: 0 }),
  clear: () => set({ messages: [], pending: null, typing: false }),
}))
