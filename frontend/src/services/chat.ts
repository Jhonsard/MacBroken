import { api } from "@/lib/api"

export const chatService = {
  async history(limit = 50, offset = 0) {
    const { data } = await api.get("/chat/history", { params: { limit, offset } })
    return data as {
      items: Array<{ id: string; message: string; response: string; timestamp: string }>
      total: number
      limit: number
      offset: number
    }
  },
}
