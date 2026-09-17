import { api } from "@/lib/api"
import type { LoginResponse, TokenPair, User } from "@/types"

export interface RegisterPayload {
  username: string
  email: string
  password: string
}

export const authService = {
  async register(payload: RegisterPayload): Promise<User> {
    const { data } = await api.post<User>("/auth/register", payload)
    return data
  },
  async login(username: string, password: string): Promise<LoginResponse> {
    const { data } = await api.post<LoginResponse>("/auth/login", { username, password })
    return data
  },
  async me(): Promise<User> {
    const { data } = await api.get<User>("/auth/me")
    return data
  },
  async refresh(refreshToken: string): Promise<TokenPair> {
    const { data } = await api.post<TokenPair>("/auth/refresh", { refresh_token: refreshToken })
    return data
  },
}