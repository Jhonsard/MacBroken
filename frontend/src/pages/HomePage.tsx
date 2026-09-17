import { Link } from "react-router-dom"

import RotatingEarth from "@/components/ui/wireframe-dotted-globe"
import { Button } from "@/components/ui/button"

export function HomePage() {
  return (
    <div className="relative min-h-screen overflow-hidden bg-bg-main bg-grid">
      <div className="pointer-events-none absolute inset-0 opacity-50">
        <RotatingEarth width={1100} height={900} />
      </div>
      <div className="pointer-events-none absolute inset-0 bg-fade-bottom" />

      <div className="relative z-10 mx-auto flex min-h-screen max-w-4xl flex-col items-center justify-center px-6 text-center">
        <p className="mb-3 font-mono text-xs tracking-[0.4em] text-accent">
          ANONYMITY · LAYER 2
        </p>
        <h1 className="text-5xl font-bold tracking-tight text-text-primary md:text-6xl">
          Spoof your MAC.
          <br />
          <span className="text-accent">Own your identity.</span>
        </h1>
        <p className="mt-6 max-w-xl text-base text-text-secondary">
          Changez votre adresse MAC à la volée, journalisez chaque opération,
          et gardez le contrôle sur votre présence réseau.
        </p>

        <div className="mt-10 flex gap-4">
          <Button asChild size="lg">
            <Link to="/signup">Get Started</Link>
          </Button>
          <Button asChild variant="outline" size="lg">
            <Link to="/login">Log In</Link>
          </Button>
        </div>

        <p className="mt-16 font-mono text-[11px] text-text-dim">
          © 2026 MAC Spoofing Platform — Built with FastAPI + Celery + React
        </p>
      </div>
    </div>
  )
}