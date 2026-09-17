import { Navigate, Outlet, useLocation } from "react-router-dom"

import { useAuthStore } from "@/stores/authStore"

export function ProtectedRoute() {
  const { accessToken, hydrated } = useAuthStore()
  const location = useLocation()

  if (!hydrated) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-bg-main">
        <span className="text-xs font-mono text-text-dim animate-pulse-glow">
          [auth] hydrating…
        </span>
      </div>
    )
  }

  if (!accessToken) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />
  }

  return <Outlet />
}