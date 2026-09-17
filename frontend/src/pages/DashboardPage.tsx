import { Loader2, RefreshCw, ShieldCheck } from "lucide-react"
import { useCallback, useEffect, useState } from "react"

import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { extractErrorMessage } from "@/lib/api"
import { macService } from "@/services/mac"
import { useAuthStore } from "@/stores/authStore"
import type {
  InterfaceInfo,
  MacHistoryItem,
  SpoofResponse,
} from "@/types"

export function DashboardPage() {
  const user = useAuthStore((s) => s.user)

  const [interfaces, setInterfaces] = useState<InterfaceInfo[]>([])
  const [history, setHistory] = useState<MacHistoryItem[]>([])
  const [dryRun, setDryRun] = useState(true)
  const [selectedIface, setSelectedIface] = useState<string>("")
  const [targetMac, setTargetMac] = useState<string>("")
  const [loading, setLoading] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [feedback, setFeedback] = useState<{ tone: "ok" | "err"; msg: string } | null>(
    null,
  )
  const [lastTask, setLastTask] = useState<SpoofResponse | null>(null)

  const refresh = useCallback(async () => {
    setLoading(true)
    setFeedback(null)
    try {
      const [ifaces, hist] = await Promise.all([
        macService.listInterfaces(),
        macService.history(20, 0),
      ])
      setInterfaces(ifaces.interfaces)
      setDryRun(ifaces.dry_run)
      setHistory(hist.items)
      const spoofable = ifaces.interfaces.find((i) => i.is_spoofable)
      if (spoofable && !selectedIface) setSelectedIface(spoofable.name)
    } catch (err) {
      setFeedback({ tone: "err", msg: extractErrorMessage(err) })
    } finally {
      setLoading(false)
    }
  }, [selectedIface])

  useEffect(() => {
    void refresh()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const handleSpoof = async () => {
    if (!selectedIface) return
    setSubmitting(true)
    setFeedback(null)
    try {
      const res = await macService.spoof(
        selectedIface,
        targetMac.trim() || undefined,
      )
      setLastTask(res)
      setFeedback({
        tone: "ok",
        msg: `Tâche enqueued : ${res.task_id.slice(0, 8)}…`,
      })
      setTargetMac("")

      let state = "PENDING"
      let attempts = 0
      while (state === "PENDING" || state === "STARTED") {
        if (attempts++ > 20) break
        await new Promise((r) => setTimeout(r, 500))
        const st = await macService.taskStatus(res.task_id)
        state = st.state
        if (st.ready) {
          if (st.successful) {
            setFeedback({
              tone: "ok",
              msg: `Spoof ${st.result?.dry_run ? "(dry-run) " : ""}SUCCESS.`,
            })
          } else {
            setFeedback({ tone: "err", msg: st.error ?? "Échec de la tâche." })
          }
          break
        }
      }
      await refresh()
    } catch (err) {
      setFeedback({ tone: "err", msg: extractErrorMessage(err) })
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="space-y-8">
      <div className="flex items-end justify-between">
        <div>
          <h1 className="text-2xl font-bold text-text-primary">Dashboard</h1>
          <p className="mt-1 text-sm text-text-secondary">
            Bienvenue, <span className="text-accent">{user?.username}</span>.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <span
            className={`inline-flex items-center gap-2 rounded-full border px-3 py-1 text-xs font-mono ${
              dryRun
                ? "border-warning/40 text-warning"
                : "border-accent/40 text-accent"
            }`}
          >
            <ShieldCheck className="h-3 w-3" />
            {dryRun ? "DRY-RUN" : "LIVE"}
          </span>
          <Button variant="ghost" size="sm" onClick={refresh} disabled={loading}>
            {loading ? (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            ) : (
              <RefreshCw className="mr-2 h-4 w-4" />
            )}
            Refresh
          </Button>
        </div>
      </div>

      {feedback && (
        <div
          className={`rounded-md border px-4 py-3 text-sm ${
            feedback.tone === "ok"
              ? "border-accent/40 bg-accent/5 text-accent"
              : "border-danger/40 bg-danger/5 text-danger"
          }`}
        >
          {feedback.msg}
        </div>
      )}

      <div className="grid gap-6 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Interfaces réseau</CardTitle>
            <CardDescription>
              Détectées à l'instant via le worker. Seules les interfaces
              `spoofable` peuvent être ciblées.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {interfaces.length === 0 && (
                <p className="text-sm text-text-dim">Aucune interface détectée.</p>
              )}
              {interfaces.map((iface) => (
                <div
                  key={iface.name}
                  className="flex items-center justify-between rounded-md border border-border bg-bg-input/50 px-4 py-3"
                >
                  <div className="flex items-center gap-3">
                    <span
                      className={`h-2 w-2 rounded-full ${
                        iface.is_spoofable ? "bg-accent" : "bg-text-dim"
                      }`}
                    />
                    <div>
                      <div className="font-mono text-sm text-text-primary">
                        {iface.name}
                      </div>
                      <div className="font-mono text-[11px] text-text-dim">
                        {iface.mac}
                      </div>
                    </div>
                  </div>
                  <div className="text-right text-[11px]">
                    <div className="text-text-muted">{iface.state}</div>
                    {!iface.is_spoofable && (
                      <div className="text-danger">{iface.reason}</div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Nouveau spoof</CardTitle>
            <CardDescription>
              MAC cible vide = générée aléatoirement (locally-administered).
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="iface">Interface</Label>
              <select
                id="iface"
                value={selectedIface}
                onChange={(e) => setSelectedIface(e.target.value)}
                className="flex h-11 w-full rounded-md border border-border bg-bg-input px-3 text-sm text-text-primary focus:border-accent focus:outline-none"
              >
                <option value="">— sélectionner —</option>
                {interfaces
                  .filter((i) => i.is_spoofable)
                  .map((i) => (
                    <option key={i.name} value={i.name}>
                      {i.name} ({i.mac})
                    </option>
                  ))}
              </select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="mac">MAC cible (optionnel)</Label>
              <Input
                id="mac"
                type="text"
                placeholder="aa:bb:cc:dd:ee:ff"
                value={targetMac}
                onChange={(e) => setTargetMac(e.target.value)}
                pattern="^([0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}$"
              />
            </div>

            <Button
              onClick={handleSpoof}
              disabled={submitting || !selectedIface}
              className="w-full"
            >
              {submitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              Lancer le spoof
            </Button>

            {lastTask && (
              <div className="rounded-md border border-border bg-bg-input/50 p-3 font-mono text-[11px] text-text-dim">
                <div>task: {lastTask.task_id}</div>
                <div>entry: {lastTask.entry_id}</div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Historique</CardTitle>
          <CardDescription>20 dernières opérations.</CardDescription>
        </CardHeader>
        <CardContent>
          {history.length === 0 ? (
            <p className="text-sm text-text-dim">Aucune opération enregistrée.</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="border-b border-border text-[11px] font-mono uppercase tracking-wider text-text-dim">
                    <th className="py-2 pr-4">Interface</th>
                    <th className="py-2 pr-4">Original</th>
                    <th className="py-2 pr-4">Spoofed</th>
                    <th className="py-2 pr-4">Statut</th>
                    <th className="py-2">Date</th>
                  </tr>
                </thead>
                <tbody className="font-mono text-[12px]">
                  {history.map((h) => (
                    <tr key={h.id} className="border-b border-border/50">
                      <td className="py-2 pr-4 text-text-primary">
                        {h.interface_name}
                      </td>
                      <td className="py-2 pr-4 text-text-muted">{h.original_mac}</td>
                      <td className="py-2 pr-4 text-accent">{h.spoofed_mac}</td>
                      <td className="py-2 pr-4">
                        <span
                          className={
                            h.status === "SUCCESS"
                              ? "text-accent"
                              : h.status === "FAILED"
                                ? "text-danger"
                                : "text-warning"
                          }
                        >
                          {h.status}
                        </span>
                      </td>
                      <td className="py-2 text-text-dim">
                        {new Date(h.timestamp).toLocaleString()}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}