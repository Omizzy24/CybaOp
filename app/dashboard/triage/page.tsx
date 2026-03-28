"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { TopNav, BottomNav } from "../components/nav";

interface Incident {
  incident_type: string;
  severity: "critical" | "warning" | "info" | "healthy";
  title: string;
  detail: string;
  track_id: string | null;
  track_title: string | null;
  metric_value: number;
  threshold: number;
  remediation: string;
}

interface TriageData {
  overall_status: "critical" | "warning" | "info" | "healthy";
  incident_count: number;
  critical_count: number;
  warning_count: number;
  incidents: Incident[];
  catalog_uptime: number;
  last_release_days_ago: number | null;
}

const STATUS_CONFIG = {
  critical: { label: "Critical", color: "text-rose", bg: "bg-rose-dim", border: "border-rose/30", dot: "bg-rose", pulse: true },
  warning: { label: "Degraded", color: "text-amber", bg: "bg-amber-dim", border: "border-amber/30", dot: "bg-amber", pulse: false },
  info: { label: "Monitoring", color: "text-sky", bg: "bg-sky-dim", border: "border-sky/30", dot: "bg-sky", pulse: false },
  healthy: { label: "All Systems Nominal", color: "text-lime", bg: "bg-lime-dim", border: "border-lime/30", dot: "bg-lime", pulse: false },
} as const;

const SEVERITY_ICON = { critical: "🔴", warning: "🟡", info: "🔵", healthy: "🟢" } as const;

export default function TriagePage() {
  const [triage, setTriage] = useState<TriageData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();

  const fetchTriage = useCallback(() => {
    setLoading(true);
    setError(null);
    fetch("/api/triage")
      .then((r) => { if (r.status === 401) { router.push("/?error=auth_failed"); return null; } return r.json(); })
      .then((j) => {
        if (!j) return;
        if (j.success === false) setError(j.message || "Triage failed");
        else setTriage(j.triage);
        setLoading(false);
      })
      .catch(() => { setError("Failed to connect"); setLoading(false); });
  }, [router]);

  useEffect(() => { fetchTriage(); }, [fetchTriage]);

  return (
    <div className="min-h-screen pb-20 md:pb-0">
      <TopNav />
      <div className="md:hidden px-4 pt-4 pb-2 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <a href="/dashboard" className="text-lg font-bold">Cyba<span className="text-accent">Op</span></a>
          <span className="text-xs text-muted">/ triage</span>
        </div>
        <a href="/dashboard" className="text-xs text-muted">← Back</a>
      </div>

      <div className="max-w-4xl mx-auto px-4 sm:px-6 py-6 sm:py-10 space-y-6 animate-page-enter">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold font-mono">Catalog Status</h1>
          <p className="text-muted text-sm mt-1 font-mono">Production health monitoring for your tracks</p>
        </div>

        {loading ? <TriageSkeleton /> : error ? (
          <div className="rounded-xl border border-border bg-surface p-8 text-center space-y-4">
            <p className="text-muted font-mono text-sm">{error}</p>
            <button onClick={fetchTriage} className="px-4 py-2 bg-accent hover:bg-accent-hover text-white rounded-lg text-sm font-mono">Retry</button>
          </div>
        ) : triage ? <TriageContent triage={triage} onRefresh={fetchTriage} /> : null}
      </div>
      <BottomNav />
    </div>
  );
}

function TriageContent({ triage, onRefresh }: { triage: TriageData; onRefresh: () => void }) {
  const status = STATUS_CONFIG[triage.overall_status];
  const uptime = (triage.catalog_uptime * 100).toFixed(1);

  return (
    <div className="space-y-6">
      {/* Status banner */}
      <div className={`rounded-xl border ${status.border} ${status.bg} p-5 sm:p-6`}>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className={`w-3 h-3 rounded-full ${status.dot} ${status.pulse ? "animate-pulse" : ""}`} />
            <div>
              <p className={`text-lg font-bold font-mono ${status.color}`}>{status.label}</p>
              <p className="text-xs text-muted font-mono mt-0.5">
                {triage.incident_count === 0 ? "No incidents detected" : `${triage.incident_count} incident${triage.incident_count > 1 ? "s" : ""} detected`}
              </p>
            </div>
          </div>
          <button onClick={onRefresh} className="text-xs text-muted hover:text-foreground font-mono px-3 py-1.5 rounded-lg border border-border hover:border-muted">Re-scan</button>
        </div>
      </div>

      {/* Metrics strip */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <MetricBox label="Catalog Uptime" value={`${uptime}%`} color={parseFloat(uptime) > 80 ? "text-lime" : parseFloat(uptime) > 50 ? "text-amber" : "text-rose"} />
        <MetricBox label="Critical" value={String(triage.critical_count)} color={triage.critical_count > 0 ? "text-rose" : "text-muted"} />
        <MetricBox label="Warnings" value={String(triage.warning_count)} color={triage.warning_count > 0 ? "text-amber" : "text-muted"} />
        <MetricBox label="Last Release" value={triage.last_release_days_ago !== null ? `${triage.last_release_days_ago}d ago` : "—"} color={triage.last_release_days_ago && triage.last_release_days_ago > 60 ? "text-amber" : "text-muted"} />
      </div>

      {/* Incident feed */}
      {triage.incidents.length > 0 && (
        <div className="space-y-2">
          <h2 className="text-sm font-semibold font-mono uppercase tracking-wider text-muted">Incident Log</h2>
          <div className="space-y-2 stagger-children">
            {triage.incidents.map((incident, i) => (
              <IncidentRow key={i} incident={incident} />
            ))}
          </div>
        </div>
      )}

      {triage.incidents.length === 0 && (
        <div className="rounded-xl border border-lime/20 bg-lime-dim p-8 text-center">
          <p className="text-lime font-mono text-sm">All clear. Your catalog is healthy.</p>
          <p className="text-xs text-muted font-mono mt-1">Check back after your next release or when you want to monitor changes.</p>
        </div>
      )}
    </div>
  );
}

function IncidentRow({ incident }: { incident: Incident }) {
  const [expanded, setExpanded] = useState(false);
  const sev = STATUS_CONFIG[incident.severity] || STATUS_CONFIG.info;
  const icon = SEVERITY_ICON[incident.severity] || "⚪";

  return (
    <div className={`rounded-xl border ${sev.border} ${sev.bg} overflow-hidden`}>
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full text-left px-4 py-3 flex items-center gap-3"
      >
        <span className="text-sm flex-shrink-0">{icon}</span>
        <div className="flex-1 min-w-0">
          <p className="text-sm font-mono font-medium truncate">{incident.title}</p>
          <p className="text-xs text-muted font-mono truncate">{incident.detail}</p>
        </div>
        <span className={`text-[10px] px-2 py-0.5 rounded-full font-mono uppercase tracking-wider ${sev.color} ${sev.bg} border ${sev.border} flex-shrink-0`}>
          {incident.severity}
        </span>
        <span className="text-muted text-xs flex-shrink-0">{expanded ? "▲" : "▼"}</span>
      </button>

      {expanded && (
        <div className="px-4 pb-4 space-y-3 border-t border-border/50 pt-3">
          <div className="space-y-1">
            <p className="text-[10px] text-muted font-mono uppercase tracking-wider">Detail</p>
            <p className="text-sm text-muted">{incident.detail}</p>
          </div>

          {incident.metric_value > 0 && (
            <div className="flex gap-4">
              <div>
                <p className="text-[10px] text-muted font-mono uppercase">Measured</p>
                <p className="text-sm font-mono font-bold">{formatMetric(incident.metric_value)}</p>
              </div>
              <div>
                <p className="text-[10px] text-muted font-mono uppercase">Threshold</p>
                <p className="text-sm font-mono text-muted">{formatMetric(incident.threshold)}</p>
              </div>
            </div>
          )}

          {incident.remediation && (
            <div className="rounded-lg bg-background/50 border border-border p-3">
              <p className="text-[10px] text-accent font-mono uppercase tracking-wider mb-1">Remediation</p>
              <p className="text-xs text-foreground leading-relaxed">{incident.remediation}</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function MetricBox({ label, value, color }: { label: string; value: string; color: string }) {
  return (
    <div className="rounded-xl border border-border bg-surface p-3 text-center">
      <p className="text-[10px] text-muted font-mono uppercase tracking-wider">{label}</p>
      <p className={`text-lg font-bold font-mono tabular-nums ${color}`}>{value}</p>
    </div>
  );
}

function formatMetric(v: number): string {
  if (v >= 1) return v.toLocaleString(undefined, { maximumFractionDigits: 0 });
  return `${(v * 100).toFixed(1)}%`;
}

function TriageSkeleton() {
  return (
    <div className="space-y-6">
      <div className="rounded-xl border border-border bg-surface p-6 animate-pulse"><div className="h-6 w-48 bg-border rounded" /></div>
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {[...Array(4)].map((_, i) => <div key={i} className="rounded-xl border border-border bg-surface p-3 animate-pulse"><div className="h-3 w-16 bg-border rounded mx-auto mb-2" /><div className="h-6 w-12 bg-border rounded mx-auto" /></div>)}
      </div>
      <div className="space-y-2">
        {[...Array(3)].map((_, i) => <div key={i} className="rounded-xl border border-border bg-surface p-4 animate-pulse"><div className="h-4 w-64 bg-border rounded" /></div>)}
      </div>
    </div>
  );
}
