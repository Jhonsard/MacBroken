import { Loader2 } from "lucide-react"
import { type FormEvent, useState } from "react"
import { useLocation, useNavigate } from "react-router-dom"

import { AuthLayout } from "@/components/layouts/AuthLayout"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { extractErrorMessage } from "@/lib/api"
import { authService } from "@/services/auth"
import { useAuthStore } from "@/stores/authStore"

export function LoginPage() {
  const navigate = useNavigate()
  const location = useLocation() as { state?: { from?: string } }
  const setSession = useAuthStore((s) => s.setSession)

  const [username, setUsername] = useState("")
  const [password, setPassword] = useState("")
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setError(null)
    setLoading(true)
    try {
      const res = await authService.login(username.trim(), password)
      setSession({
        user: res.user,
        access_token: res.access_token,
        refresh_token: res.refresh_token,
      })
      navigate(location.state?.from ?? "/dashboard", { replace: true })
    } catch (err) {
      setError(extractErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  return (
    <AuthLayout
      title="Log In"
      subtitle="Authentifiez-vous pour accéder à la plateforme."
      footerPrompt="Don't have an account?"
      footerLinkLabel="Sign Up"
      footerLinkTo="/signup"
    >
      <form onSubmit={handleSubmit} className="space-y-5">
        <div className="space-y-2">
          <Label htmlFor="username">Username</Label>
          <Input
            id="username"
            type="text"
            autoComplete="username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="password">Password</Label>
          <Input
            id="password"
            type="password"
            autoComplete="current-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
        </div>
        {error && (
          <div className="rounded-md border border-danger/40 bg-danger/5 px-3 py-2 text-xs text-danger">
            {error}
          </div>
        )}
        <Button type="submit" disabled={loading} className="w-full">
          {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
          Log In
        </Button>
      </form>
    </AuthLayout>
  )
}