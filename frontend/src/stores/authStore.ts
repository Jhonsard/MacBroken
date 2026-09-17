import { create } from "zustand"
import { createJSONStorage, persist } from "zustand/middleware"

import type { User } from "@/types"

interface AuthState {
  user: User | null
  accessToken: string | null
  refreshToken: string | null
  hydrated: boolean
  setSession: (p: { user: User; access_token: string; refresh_token: string }) => void
  setTokens: (access: string, refresh: string) => void
  setUser: (user: User) => void
  clear: () => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      accessToken: null,
      refreshToken: null,
      // ⚠️ localStorage est SYNCHRONE → la réhydratation est terminée
      //    dès que `create()` retourne. On peut donc marquer `hydrated`
      //    à `true` dès l'état initial.
      hydrated: true,
      setSession: ({ user, access_token, refresh_token }) =>
        set({ user, accessToken: access_token, refreshToken: refresh_token }),
      setTokens: (access, refresh) =>
        set({ accessToken: access, refreshToken: refresh }),
      setUser: (user) => set({ user }),
      clear: () => set({ user: null, accessToken: null, refreshToken: null }),
    }),
    {
      name: "mac-spoof-auth",
      storage: createJSONStorage(() => localStorage),
      partialize: (s) => ({
        user: s.user,
        accessToken: s.accessToken,
        refreshToken: s.refreshToken,
      }),
      // ❌ NE PAS utiliser `onRehydrateStorage` ici :
      //    le callback s'exécute AVANT que `useAuthStore` ne soit assigné,
      //    donc `useAuthStore.setState(...)` lève une TypeError silencieuse.
    },
  ),
)

// ------------------------------------------------------------------
// Fallback robuste : si un jour on bascule sur un storage async
// (IndexedDB, etc.), ce bloc gérera la transition.
// Pour localStorage (sync), c'est un no-op.
// ------------------------------------------------------------------
if (typeof window !== "undefined" && !useAuthStore.getState().hydrated) {
  if (useAuthStore.persist.hasHydrated()) {
    useAuthStore.setState({ hydrated: true })
  } else {
    useAuthStore.persist.onFinishHydration(() => {
      useAuthStore.setState({ hydrated: true })
    })
  }
}