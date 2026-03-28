"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter, useParams } from "next/navigation";
import { TopNav, BottomNav } from "../../components/nav";
import { WorkflowStepList } from "../../components/workflow-step-list";
import { CritiquePanel } from "../../components/critique-panel";
import { RemediationChecklist } from "../../components/remediation-checklist";
import type { WorkflowSession, WorkflowStatus } from "@/app/dashboard/types";

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

export default function WorkflowDetailPage() {
  const params = useParams();
  const id = params.id as string;
  const [user, setUser] = useState<UserData | null>(null);
  const [session, setSession] = useState<WorkflowSession | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [acting, setActing] = useState<string | null>(null);
  const router = useRouter();

  const fetchSession = useCallback(() => {
    setLoading(true);
    setError(null);

    Promise.all([
      fetch("/api/auth/me").then((r) => {
        if (r.status === 401) { router.push("/?error=auth_failed"); return null; }
        return r.json();
      }),
      fetch(`/api/workflows/${id}`).then((r) => {
        if (!r.ok) throw new Error("Failed to load workflow");
        return r.json();
      }),
    ])
      .then(([userData, sessionData]) => {
        if (!userData) return;
        setUser(userData);
        setSession(sessionData as WorkflowSession);
        setLoading(false);
      })
      .catch(() => { setError("Failed to load workflow"); setLoading(false); });
  }, [id, router]);

  useEffect(() => { fetchSession(); }, [fetchSession]);

  async function handleAction(action: string) {
    setActing(action);
    try {
      const url = `/api/workflows/${id}/${action}`;
      const body = action === "advance" ? JSON.stringify({ user_input: {} }) : undefined;
      const res = await fetch(url, {
        method: "POST",
        headers: body ? { "Content-Type": "application/json" } : {},
        body,
      });
      const data = await res.json();
      if (data.id) {
        setSession(data as WorkflowSession);
      } else {
        setError(data.message || `Failed to ${action}`);
      }
    } catch {
      setError(`Failed to ${action}`);
    } finally {
      setActing(null);
    }
  }

  async function handleLogout() {
    await fetch("/api/auth/logout", { method: "POST" });
    router.push("/");
  }

  const workflowLabel = session ? (WORKFLOW_LABELS[session.workflow_type] ?? session.workflow_type) : "Workflow";

  if (loading) {
    return (
      <div className="min-h-screen pb-20 md:pb-0">
        <TopNav user={user ?? undefined} onLogout={handleLogout} />
        <div className="md:hidden px-4 pt-4 pb-2 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <a href="/dashboard" className="text-lg font-bold">Cyba<span className="text-accent">Op</span></a>
            <span className="text-xs text-muted">/ <a href="/dashboard/workflows" className="hover:text-foreground">workflows</a> / …</span>
          </div>
          <a href="/dashboard/workflows" className="text-xs text-muted">← Back</a>
        </div>
        <div className="max-w-4xl mx-auto px-4 sm:px-6 py-6 sm:py-10">
          <DetailSkeleton />
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
          <span className="text-xs text-muted">/ <a href="/dashboard/workflows" className="hover:text-foreground">workflows</a> / {workflowLabel}</span>
        </div>
        <a href="/dashboard/workflows" className="text-xs text-muted">← Back</a>
      </div>

      <div className="max-w-4xl mx-auto px-4 sm:px-6 py-6 sm:py-10 space-y-6 animate-page-enter">
        {error ? (
          <div className="rounded-xl border border-border bg-surface p-8 text-center space-y-4">
            <p className="text-muted font-mono text-sm">{error}</p>
            <button onClick={fetchSession} className="px-4 py-2 bg-accent hover:bg-accent-hover text-white rounded-lg text-sm font-mono">Retry</button>
          </div>
        ) : session ? (
          <SessionDetail
            session={session}
            acting={acting}
            onAction={handleAction}
          />
        ) : null}
      </div>
      <BottomNav />
    </div>
  );
}

function SessionDetail({
  session,
  acting,
  onAction,
}: {
  session: WorkflowSession;
  acting: string | null;
  onAction: (action: string) => void;
}) {
  const status = STATUS_CONFIG[session.status] ?? STATUS_CONFIG.active;
  const label = WORKFLOW_LABELS[session.workflow_type] ?? session.workflow_type;
  const currentStep = session.steps.find((s) => s.step_name === session.current_step);
  const currentStepDef = currentStep ?? null;
  const isActive = session.status === "active";
  const isPaused = session.status === "paused";
  const isTerminal = session.status === "completed" || session.status === "failed";

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold font-mono">{label}</h1>
          <p className="text-muted text-sm mt-1 font-mono">
            {new Date(session.created_at).toLocaleDateString(undefined, {
              month: "short", day: "numeric", year: "numeric", hour: "2-digit", minute: "2-digit",
            })}
          </p>
        </div>
        <span className={`text-xs px-3 py-1 rounded-full font-mono uppercase tracking-wider ${status.color} ${status.bg} border ${status.border}`}>
          {status.label}
        </span>
      </div>

      {/* Progress indicator during processing */}
      {acting && (
        <div className="rounded-xl border border-amber/30 bg-amber-dim p-4 flex items-center gap-3">
          <div className="w-4 h-4 border-2 border-muted border-t-amber rounded-full animate-spin" />
          <p className="text-sm font-mono text-amber">
            {acting === "advance" && currentStep ? `Processing: ${currentStep.label}` : `${acting}…`}
          </p>
        </div>
      )}

      {/* Step sequence */}
      <div className="rounded-xl border border-border bg-surface p-4 sm:p-5">
        <p className="text-[10px] font-mono uppercase tracking-wider text-muted mb-3">Steps</p>
        <WorkflowStepList steps={session.steps} currentStep={session.current_step} />
      </div>

      {/* Current step expanded panel */}
      {currentStep && currentStep.output && (
        <CurrentStepPanel session={session} step={currentStep} />
      )}

      {/* Completed steps with output */}
      {session.steps
        .filter((s) => s.status === "completed" && s.output && s.step_name !== session.current_step)
        .map((step, i) => (
          <CompletedStepPanel key={`${step.step_name}-${i}`} session={session} step={step} />
        ))}

      {/* Action buttons */}
      {!isTerminal && (
        <div className="flex flex-wrap gap-3">
          {isActive && (
            <button
              onClick={() => onAction("advance")}
              disabled={acting !== null}
              className="px-4 py-2 bg-accent hover:bg-accent-hover text-white rounded-lg text-sm font-mono disabled:opacity-50"
            >
              {acting === "advance" ? "Advancing…" : "Advance"}
            </button>
          )}
          {isActive && currentStepDef?.skippable && (
            <button
              onClick={() => onAction("skip")}
              disabled={acting !== null}
              className="px-4 py-2 bg-surface hover:bg-surface-hover text-foreground rounded-lg text-sm font-mono border border-border disabled:opacity-50"
            >
              {acting === "skip" ? "Skipping…" : "Skip Step"}
            </button>
          )}
          {isActive && (
            <button
              onClick={() => onAction("pause")}
              disabled={acting !== null}
              className="px-4 py-2 bg-surface hover:bg-surface-hover text-amber rounded-lg text-sm font-mono border border-amber/30 disabled:opacity-50"
            >
              {acting === "pause" ? "Pausing…" : "Pause"}
            </button>
          )}
          {isPaused && (
            <button
              onClick={() => onAction("resume")}
              disabled={acting !== null}
              className="px-4 py-2 bg-accent hover:bg-accent-hover text-white rounded-lg text-sm font-mono disabled:opacity-50"
            >
              {acting === "resume" ? "Resuming…" : "Resume"}
            </button>
          )}
        </div>
      )}

      {/* Terminal state message */}
      {isTerminal && (
        <div className={`rounded-xl border ${status.border} ${status.bg} p-5 text-center`}>
          <p className={`text-sm font-mono ${status.color}`}>
            {session.status === "completed" ? "Workflow completed successfully." : "Workflow failed."}
          </p>
        </div>
      )}

      {/* Back link */}
      <a href="/dashboard/workflows" className="inline-block text-xs text-muted hover:text-foreground font-mono">
        ← Back to workflows
      </a>
    </div>
  );
}

function CurrentStepPanel({
  session,
  step,
}: {
  session: WorkflowSession;
  step: WorkflowSession["steps"][number];
}) {
  return <StepOutputPanel session={session} step={step} isCurrent />;
}

function CompletedStepPanel({
  session,
  step,
}: {
  session: WorkflowSession;
  step: WorkflowSession["steps"][number];
}) {
  return <StepOutputPanel session={session} step={step} isCurrent={false} />;
}

function StepOutputPanel({
  session,
  step,
  isCurrent,
}: {
  session: WorkflowSession;
  step: WorkflowSession["steps"][number];
  isCurrent: boolean;
}) {
  const output = step.output;
  if (!output) return null;

  // Critique panel: check if output has critique data
  const hasCritique =
    output.strength && output.weakness && output.diagnosis && output.recommendation;
  if (hasCritique) {
    return (
      <div className={isCurrent ? "" : "opacity-80"}>
        <p className="text-[10px] font-mono uppercase tracking-wider text-muted mb-2">{step.label}</p>
        <CritiquePanel
          critique={{
            strength: String(output.strength),
            weakness: String(output.weakness),
            diagnosis: String(output.diagnosis),
            recommendation: String(output.recommendation),
          }}
          trackTitle={output.track_title ? String(output.track_title) : undefined}
        />
      </div>
    );
  }

  // Remediation checklist: check if context has remediation_steps
  const remediationSteps = session.context.remediation_steps as
    | Array<{ action: string; expected_impact: string; status: string }>
    | undefined;
  const currentStepIndex = (session.context.current_step_index as number) ?? 0;
  if (remediationSteps && remediationSteps.length > 0 && step.step_name === "remediation_step") {
    return (
      <div className={isCurrent ? "" : "opacity-80"}>
        <p className="text-[10px] font-mono uppercase tracking-wider text-muted mb-2">{step.label}</p>
        <RemediationChecklist steps={remediationSteps} currentIndex={currentStepIndex} />
      </div>
    );
  }

  // Generic output: formatted JSON or text
  return (
    <div className={`rounded-xl border border-border bg-surface p-4 sm:p-5 ${isCurrent ? "" : "opacity-80"}`}>
      <p className="text-[10px] font-mono uppercase tracking-wider text-muted mb-2">{step.label}</p>
      <pre className="text-xs font-mono text-foreground whitespace-pre-wrap break-words leading-relaxed">
        {typeof output === "string" ? output : JSON.stringify(output, null, 2)}
      </pre>
    </div>
  );
}

function DetailSkeleton() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <div className="h-6 w-48 bg-border rounded animate-pulse" />
          <div className="h-3 w-32 bg-border rounded mt-2 animate-pulse" />
        </div>
        <div className="h-6 w-20 bg-border rounded-full animate-pulse" />
      </div>
      <div className="rounded-xl border border-border bg-surface p-5 animate-pulse">
        <div className="h-3 w-16 bg-border rounded mb-4" />
        {[...Array(4)].map((_, i) => (
          <div key={i} className="flex gap-3 mb-3">
            <div className="w-3 h-3 bg-border rounded-full" />
            <div className="h-4 w-40 bg-border rounded" />
          </div>
        ))}
      </div>
      <div className="flex gap-3">
        <div className="h-10 w-24 bg-border rounded-lg animate-pulse" />
        <div className="h-10 w-24 bg-border rounded-lg animate-pulse" />
      </div>
    </div>
  );
}
