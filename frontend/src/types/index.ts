export interface User {
  id: string
  username: string
  email: string
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface TokenPair {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
}

export interface LoginResponse extends TokenPair {
  user: User
}

export type MacSpoofStatus = "PENDING" | "SUCCESS" | "FAILED" | "CANCELLED"

export interface InterfaceInfo {
  name: string
  mac: string
  state: string
  is_loopback: boolean
  is_spoofable: boolean
  reason: string
}

export interface InterfaceListResponse {
  interfaces: InterfaceInfo[]
  dry_run: boolean
}

export interface CanSpoofResponse {
  allowed: boolean
  interface_name: string
  current_mac: string | null
  target_mac: string | null
  reason: string
  rate_limited: boolean
  retry_after_seconds: number
}

export interface SpoofResponse {
  task_id: string
  entry_id: string
  interface_name: string
  original_mac: string
  spoofed_mac: string
  status: MacSpoofStatus
}

export interface TaskStatusResponse {
  task_id: string
  state: string
  ready: boolean
  successful: boolean | null
  result: Record<string, unknown> | null
  error: string | null
}

export interface MacHistoryItem {
  id: string
  user_id: string
  interface_name: string
  original_mac: string
  spoofed_mac: string
  status: MacSpoofStatus
  timestamp: string
}

export interface MacHistoryListResponse {
  items: MacHistoryItem[]
  total: number
  limit: number
  offset: number
}