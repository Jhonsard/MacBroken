import { LogOut, Shield } from "lucide-react"
import { Link, Outlet, useNavigate } from "react-router-dom"

import { Button } from "@/components/ui/button"
import { useAuthStore } from "@/stores/authStore"

import { ChatWidget } from "@/components/chat/ChatWidget"

export function AppLayout() {
  const navigate = useNavigate()
  const user = useAuthStore((s) => s.user)
  const clear = useAuthStore((s) => s.clear)

  const handleLogout = () => {
    clear()
    navigate("/login", { replace: true })
  }

  return (
    <div className="min-h-screen bg-bg-main">
      <header className="border-b border-border bg-bg-content/80 backdrop-blur-xl sticky top-0 z-40">
        <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-6">
          <Link to="/dashboard" className="flex items-center gap-2">
            <Shield className="h-5 w-5 text-accent" />
            <span className="font-mono text-sm tracking-widest text-text-primary">
              MAC·SPOOF
            </span>
          </Link>
          <div className="flex items-center gap-4">
            <span className="text-xs font-mono text-text-dim">{user?.username ?? "—"}</span>
            <Button variant="ghost" size="sm" onClick={handleLogout}>
              <LogOut className="mr-2 h-4 w-4" />
              Logout
            </Button>
          </div>
        </div>
      </header>
      <main className="mx-auto max-w-7xl px-6 py-8">
        <Outlet />
      </main>

      <ChatWidget />
    </div>
  )
}
