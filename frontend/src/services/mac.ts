import { api } from "@/lib/api"
import type {
  CanSpoofResponse,
  InterfaceListResponse,
  MacHistoryListResponse,
  SpoofResponse,
  TaskStatusResponse,
} from "@/types"

export const macService = {
  async listInterfaces(): Promise<InterfaceListResponse> {
    const { data } = await api.get<InterfaceListResponse>("/mac/interfaces")
    return data
  },
  async canSpoof(interfaceName: string, spoofedMac?: string): Promise<CanSpoofResponse> {
    const { data } = await api.post<CanSpoofResponse>("/mac/can-spoof", {
      interface_name: interfaceName,
      spoofed_mac: spoofedMac ?? null,
    })
    return data
  },
  async spoof(interfaceName: string, spoofedMac?: string): Promise<SpoofResponse> {
    const { data } = await api.post<SpoofResponse>("/mac/spoof", {
      interface_name: interfaceName,
      spoofed_mac: spoofedMac ?? null,
    })
    return data
  },
  async history(limit = 50, offset = 0): Promise<MacHistoryListResponse> {
    const { data } = await api.get<MacHistoryListResponse>("/mac/history", {
      params: { limit, offset },
    })
    return data
  },
  async taskStatus(taskId: string): Promise<TaskStatusResponse> {
    const { data } = await api.get<TaskStatusResponse>(`/mac/tasks/${taskId}`)
    return data
  },
}