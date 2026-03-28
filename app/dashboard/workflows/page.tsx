"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { TopNav, BottomNav } from "../components/nav";
import { HealthScoreDisplay } from "../components/health-score-display";
import { ProTeaser } from "../components/pro-teaser";
import type {
  WorkflowSession,
  WorkflowListData,
  HealthScoreHistory,
  WorkflowStatus,
} from "@/app/dashboard/types";

interface UserData {
  username?: string;
  display_name?: string;
  avatar_url?: string;
  tier?: string;
}

const STATUS_CONFIG: Record<
  WorkflowStatus,
  { label: string; color: string; bg: string; border: string }
> = {
  active: { label: "Active", color: "text-lime", bg: "bg-lime-dim", border: "border-lime/30" },
  paused: { label: "Paused", color: "text-amber", bg: "bg-amber-dim", border: "border-amber/30" },
  completed: { label: "Completed", color: "text-sky", bg: "bg-sky-dim", border: "border-sky/30" },
  failed: { label: "Failed", color: "text-rose", bg: "bg-rose-dim", border: "border-rose/30" },
};

const WORKFLOW_LABELS: Record<string, string> = {
  portfolio_critique: "Portfolio Critique",
  remediation: "Remediation Pipeline",
  release_planner: "Release Planner",
};

const WORKFLOW_ICONS: Record<string, string> = {
  portfolio_critique: "🎵",
  remediation: "🔧",
  release_planner: "📅",
};

export default function WorkflowsPage() {
  const [user, setUser] = useState<UserData | null>(null);
  const [sessions, setSessions] = useState<WorkflowSession[]>([]);
  const [healthScore, setHealthScore] = useState<HealthScoreHistory | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [creating, setCreating] = useState<string | null>(null);
  const router = useRouter();

  const fetchData = useCallback(() => {
    setLoading(true);
    setError(null);

    Promise.all([
      fetch("/api/auth/me").then((r) => {
        if (r.status === 401) { router.push("/?error=auth_failed"); return null; }
        return r.json();
      }),
      fetch("/api/workflows").then((r) => r.json()).catch(() => ({ sessions: [], total: 0 })),
      fetch("/api/health-score").then((r) => r.json()).catch(() => null),
    ])
      .then(([userData, workflowData, healthData]) => {
        if (!userData) return;
        if (userData.error) { setError(userData.message || "Auth failed"); setLoading(false); return; }
        setUser(userData);
        const wf = workflowData as WorkflowListData;
        setSessions(wf.sessions ?? []);
        if (healthData && !healthData.error) setHealthScore(healthData as HealthScoreHistory);
        setLoading(false);
      })
      .catch(() => { setError("Failed to connect"); setLoading(false); });
  }, [router]);

  useEffect(() => { fetchData(); }, [fetchData]);

  async function handleCreate(workflowType: string) {
    setCreating(workflowType);
    try {
      const res = await fetch("/api/workflows", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ workflow_type: workflowType, params: {} }),
      });
      const data = await res.json();
      if (data.id) {
        router.push(`/dashboard/workflows/${data.id}`);
      } else {
        setError(data.message || "Failed to create workflow");
        setCreating(null);
      }
    } catch {
      setError("Failed to create workflow");
      setCreating(null);
    }
  }

  async function handleLogout() {
    await fetch("/api/auth/logout", { method: "POST" });
    router.push("/");
  }

  if (loading) {
    return (
      <div className="min-h-screen pb-20 md:pb-0">
        <TopNav user={user ?? undefined} onLogout={handleLogout} />
        <div className="md:hidden px-4 pt-4 pb-2 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <a href="/dashboard" className="text-lg font-bold">Cyba<span className="text-accent">Op</span></a>
            <span className="text-xs text-muted">/ workflows</span>
          </div>
          <a href="/dashboard" className="text-xs text-muted">← Back</a>
        </div>
        <div className="max-w-4xl mx-auto px-4 sm:px-6 py-6 sm:py-10">
          <WorkflowsSkeleton />
        </div>
        <BottomNav />
      </div>
    );
  }

  // Pro tier gating
  if (user && user.tier === "free") {
    return (
      <div className="min-h-screen pb-20 md:pb-0">
        <TopNav user={user} onLogout={handleLogout} />
        <div className="md:hidden px-4 pt-4 pb-2 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <a href="/dashboard" className="text-lg font-bold">Cyba<span className="text-accent">Op</span></a>
            <span className="text-xs text-muted">/ workflows</span>
          </div>
          <a href="/dashboard" className="text-xs text-muted">← Back</a>
        </div>
        <div className="max-w-4xl mx-auto px-4 sm:px-6 py-6 sm:py-10 space-y-6 animate-page-enter">
          <div>
            <h1 className="text-xl sm:text-2xl font-bold font-mono">Workflows</h1>
            <p className="text-muted text-sm mt-1 font-mono">Multi-step guided analysis sessions</p>
          </div>
          <ProTeaser
            icon="⚙️"
            title="Creator Workflows"
            description="Unlock portfolio critiques, remediation pipelines, and release planning with guided AI workflows."
            featureId="workflows"
          />
        </div>
        <BottomNav />
      </div>
    );
  }

  return (
    <div className="min-h-screen pb-20 md:pb-0">
      <TopNav user={user ?? undefined} onLogout={handleLogout} />
      <div className="md:hidden px-4 pt-4 pb-2 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <a href="/dashboard" className="text-lg font-bold">Cyba<span className="text-accent">Op</span></a>
          <span className="text-xs text-muted">/ workflows</span>
        </div>
        <a href="/dashboard" className="text-xs text-muted">← Back</a>
      </div>

      <div className="max-w-4xl mx-auto px-4 sm:px-6 py-6 sm:py-10 space-y-6 animate-page-enter">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold font-mono">Workflows</h1>
          <p className="text-muted text-sm mt-1 font-mono">Multi-step guided analysis sessions</p>
        </div>

        {error ? (
          <div className="rounded-xl border border-border bg-surface p-8 text-center space-y-4">
            <p className="text-muted font-mono text-sm">{error}</p>
            <button onClick={fetchData} className="px-4 py-2 bg-accent hover:bg-accent-hover text-white rounded-lg text-sm font-mono">Retry</button>
          </div>
        ) : (
          <>
            {/* Health Score */}
            {healthScore && (
              <div className="rounded-xl border border-border bg-surface p-5 sm:p-6 space-y-2">
                <p className="text-[10px] font-mono uppercase tracking-wider text-muted">Portfolio Health</p>
                <HealthScoreDisplay
                  score={healthScore.current_score}
                  history={healthScore.history}
                />
              </div>
            )}

            {/* Create Workflow Buttons */}
            <div className="space-y-2">
              <h2 className="text-sm font-semibold font-mono uppercase tracking-wider text-muted">New Workflow</h2>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                {(["portfolio_critique", "remediation", "release_planner"] as const).map((type) => (
                  <button
                    key={type}
                    onClick={() => handleCreate(type)}
                    disabled={creating !== null}
                    className="rounded-xl border border-border bg-surface hover:bg-surface-hover p-4 text-left space-y-1 card-lift disabled:opacity-50"
                  >
                    <div className="flex items-center gap-2">
                      <span>{WORKFLOW_ICONS[type]}</span>
                      <span className="text-sm font-mono font-medium">{WORKFLOW_LABELS[type]}</span>
                    </div>
                    {creating === type && (
                      <div className="flex items-center gap-2 text-xs text-muted font-mono">
                        <div className="w-3 h-3 border border-muted border-t-accent rounded-full animate-spin" />
                        Creating…
                      </div>
                    )}
                  </button>
                ))}
              </div>
            </div>

            {/* Session List */}
            {sessions.length > 0 ? (
              <div className="space-y-2">
                <h2 className="text-sm font-semibold font-mono uppercase tracking-wider text-muted">Sessions</h2>
                <div className="space-y-2 stagger-children">
                  {sessions.map((session) => (
                    <SessionCard key={session.id} session={session} />
                  ))}
                </div>
              </div>
            ) : (
              <div className="rounded-xl border border-border bg-surface p-8 text-center">
                <p className="text-muted font-mono text-sm">No workflows yet. Create one above to get started.</p>
              </div>
            )}
          </>
        )}
      </div>
      <BottomNav />
    </div>
  );
}

function SessionCard({ session }: { session: WorkflowSession }) {
  const status = STATUS_CONFIG[session.status] ?? STATUS_CONFIG.active;
  const label = WORKFLOW_LABELS[session.workflow_type] ?? session.workflow_type;
  const icon = WORKFLOW_ICONS[session.workflow_type] ?? "⚙️";
  const currentStep = session.steps.find((s) => s.step_name === session.current_step);
  const created = new Date(session.created_at).toLocaleDateString(undefined, {
    month: "short", day: "numeric", hour: "2-digit", minute: "2-digit",
  });

  return (
    <a
      href={`/dashboard/workflows/${session.id}`}
      className={`block rounded-xl border ${status.border} ${status.bg} p-4 space-y-2 card-lift`}
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2 min-w-0">
          <span className="text-sm flex-shrink-0">{icon}</span>
          <p className="text-sm font-mono font-medium truncate">{label}</p>
        </div>
        <span className={`text-[10px] px-2 py-0.5 rounded-full font-mono uppercase tracking-wider ${status.color} ${status.bg} border ${status.border} flex-shrink-0`}>
          {status.label}
        </span>
      </div>
      <div className="flex items-center justify-between text-xs text-muted font-mono">
        <span>{currentStep ? currentStep.label : session.status === "completed" ? "Done" : "—"}</span>
        <span>{created}</span>
      </div>
    </a>
  );
}

function WorkflowsSkeleton() {
  return (
    <div className="space-y-6">
      <div className="rounded-xl border border-border bg-surface p-6 animate-pulse">
        <div className="h-3 w-24 bg-border rounded mb-3" />
        <div className="h-12 w-20 bg-border rounded" />
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        {[...Array(3)].map((_, i) => (
          <div key={i} className="rounded-xl border border-border bg-surface p-4 animate-pulse">
            <div className="h-4 w-32 bg-border rounded" />
          </div>
        ))}
      </div>
      <div className="space-y-2">
        {[...Array(3)].map((_, i) => (
          <div key={i} className="rounded-xl border border-border bg-surface p-4 animate-pulse">
            <div className="h-4 w-48 bg-border rounded mb-2" />
            <div className="h-3 w-32 bg-border rounded" />
          </div>
        ))}
      </div>
    </div>
  );
}
