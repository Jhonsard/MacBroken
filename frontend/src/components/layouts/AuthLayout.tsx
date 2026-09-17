import { Link } from "react-router-dom"

import RotatingEarth from "@/components/ui/wireframe-dotted-globe"

interface AuthLayoutProps {
  title: string
  subtitle?: string
  footerPrompt?: string
  footerLinkLabel?: string
  footerLinkTo?: string
  children: React.ReactNode
}

export function AuthLayout({
  title,
  subtitle,
  footerPrompt,
  footerLinkLabel,
  footerLinkTo,
  children,
}: AuthLayoutProps) {
  return (
    <div className="relative min-h-screen w-full overflow-hidden bg-bg-main bg-grid">
      <div className="pointer-events-none absolute inset-0 opacity-40">
        <RotatingEarth width={900} height={700} className="!h-full" />
      </div>
      <div className="pointer-events-none absolute inset-0 bg-fade-bottom" />

      <div className="relative z-10 flex min-h-screen flex-col items-center justify-center px-4 py-10">
        <div className="mb-8 flex w-full max-w-md items-center justify-between">
          <Link to="/" className="font-mono text-accent text-sm tracking-widest">
            [ MAC·SPOOF ]
          </Link>
          {footerPrompt && footerLinkLabel && footerLinkTo && (
            <span className="text-xs text-text-muted">
              {footerPrompt}{" "}
              <Link
                to={footerLinkTo}
                className="text-text-primary underline underline-offset-2 hover:text-accent"
              >
                {footerLinkLabel}
              </Link>
            </span>
          )}
        </div>

        <div className="w-full max-w-md rounded-card border border-border bg-bg-card/85 backdrop-blur-2xl shadow-glow p-8">
          <div className="mb-6">
            <h1 className="text-2xl font-bold text-text-primary">{title}</h1>
            {subtitle && <p className="mt-2 text-sm text-text-secondary">{subtitle}</p>}
          </div>
          {children}
        </div>

        <p className="mt-8 text-[11px] font-mono text-text-dim">
          © 2026 MAC Spoofing Platform
        </p>
      </div>
    </div>
  )
}