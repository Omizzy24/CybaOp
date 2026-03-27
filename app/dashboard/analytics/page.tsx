"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { TopNav, BottomNav } from "../components/nav";
import { EngagementBarChart, ReleaseDayHeatmap, PlaysOverTimeChart } from "../components/charts";
import { ProgressRing } from "../components/progress-ring";
import { StreakBadge } from "../components/streak";
import { InsightCard } from "../components/insight-card";
import { ProTeaser } from "../components/pro-teaser";
import { TrackTable } from "../components/track-table";
import type { AnalyticsData, Report, HistoryPoint } from "../types";

export default function Analytics() {
  const [data, setData] = useState<AnalyticsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();

  const fetchAnalytics = useCallback(() => {
    setLoading(true);
    setError(null);
    fetch("/api/analytics")
      .then((res) => {
        if (res.status === 401) { router.push("/?error=auth_failed"); return null; }
        return res.json();
      })
      .then((json) => {
        if (!json) return;
        if (json.success === false) setError(json.message || "Failed to load analytics");
        else setData(json);
        setLoading(false);
      })
      .catch(() => { setError("Failed to connect to analytics service"); setLoading(false); });
  }, [router]);

  useEffect(() => { fetchAnalytics(); }, [fetchAnalytics]);

  return (
    <div className="min-h-screen pb-20 md:pb-0">
      <TopNav />
      <MobileHeader />
      <div className="max-w-5xl mx-auto px-4 sm:px-6 py-6 sm:py-10 space-y-6 sm:space-y-8 animate-page-enter">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h1 className="text-xl sm:text-2xl font-bold">Analytics</h1>
            <p className="text-muted text-sm mt-1">Performance, trends, and catalog insights</p>
          </div>
          <StreakBadge />
        </div>
        {loading ? <LoadingSkeleton /> : error ? <ErrorState message={error} onRetry={fetchAnalytics} /> : data?.report ? <AnalyticsContent report={data.report} processingMs={data.processing_time_ms} /> : <ErrorState message="No data available" onRetry={fetchAnalytics} />}
      </div>
      <BottomNav />
    </div>
  );
}

function MobileHeader() {
  return (
    <div className="md:hidden px-4 pt-4 pb-2 flex items-center justify-between">
      <div className="flex items-center gap-2">
        <a href="/dashboard" className="text-lg font-bold">Cyba<span className="text-accent">Op</span></a>
        <span className="text-xs text-muted">/ analytics</span>
      </div>
      <a href="/dashboard" className="text-xs text-muted">← Back</a>
    </div>
  );
}

function AnalyticsContent({ report, processingMs }: { report: Report; processingMs?: number }) {
  const { metrics, trends, eras, era_fingerprint } = report;
  const allTracks = metrics?.all_track_metrics || report.top_tracks || [];
  const concentration = metrics?.catalog_concentration || 0;
  const topN = Math.max(1, Math.ceil(allTracks.length * 0.2));

  const [history, setHistory] = useState<HistoryPoint[]>([]);
  useEffect(() => {
    fetch("/api/analytics/history")
      .then((r) => r.ok ? r.json() : null)
      .then((j) => { if (j?.success && j.data) setHistory(j.data); })
      .catch(() => {});
  }, []);

  const maxPlays = Math.max(metrics?.total_plays || 1, 1);

  return (
    <div className="space-y-6 sm:space-y-8">
      <PipelineBadge report={report} processingMs={processingMs} />

      {metrics && <MetricsRings metrics={metrics} maxPlays={maxPlays} />}

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 sm:gap-4">
        <InsightCard icon="📅" title="Best Release Window" borderColor="border-sky/20" bgColor="bg-sky-dim">
          {trends?.best_release_day ? (
            <p className="text-sm text-muted">
              Tracks on <span className="text-foreground font-medium">{trends.best_release_day}s</span> get the highest engagement.
              {trends.best_release_hour !== null && <> Best hour: <span className="text-foreground font-medium">{trends.best_release_hour}:00</span>.</>}
            </p>
          ) : <p className="text-xs text-muted">Not enough data yet.</p>}
        </InsightCard>
        <InsightCard icon="🏥" title="Catalog Health" borderColor="border-lime/20" bgColor="bg-lime-dim">
          {metrics && metrics.total_plays > 0 ? (
            <p className="text-sm text-muted">
              Top {topN} track{topN > 1 ? "s" : ""}: <span className="text-foreground font-medium">{(concentration * 100).toFixed(0)}%</span> of plays.
              {concentration > 0.8 ? " High concentration." : concentration > 0.5 ? " Healthy spread." : " Well distributed."}
            </p>
          ) : <p className="text-xs text-muted">No play data yet.</p>}
        </InsightCard>
      </div>

      {eras && eras.length > 0 && <EraTimeline eras={eras} fingerprint={era_fingerprint} />}

      {era_fingerprint && <EraFingerprint fp={era_fingerprint} />}

      {trends?.strongest_era_description && !eras?.length && (
        <InsightCard icon="🔥" title="Your Strongest Era" borderColor="border-rose/20" bgColor="bg-rose-dim">
          <p className="text-sm text-muted">{trends.strongest_era_description}</p>
        </InsightCard>
      )}

      {history.length > 0 && <PlaysOverTimeChart data={history} />}

      {allTracks.length > 0 && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-3 sm:gap-4">
          <EngagementBarChart tracks={allTracks} />
          <ReleaseDayHeatmap dayData={buildDayData(trends?.best_release_day)} bestDay={trends?.best_release_day || null} />
        </div>
      )}

      <TrackTable tracks={allTracks} />

      <div className="space-y-3">
        <h2 className="text-lg font-semibold text-muted">Pro Features</h2>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 sm:gap-4 stagger-children">
          <ProTeaser icon="📉" title="Engagement Decay" description="See how plays drop off after release." featureId="engagement_decay" />
          <ProTeaser icon="🤖" title="AI Strategy" description="Personalized release recommendations." featureId="ai_strategy" />
          <ProTeaser icon="🔍" title="Benchmarking" description="Compare to similar artists." featureId="benchmarking" />
        </div>
      </div>
    </div>
  );
}

function PipelineBadge({ report, processingMs }: { report: Report; processingMs?: number }) {
  return (
    <div className="flex flex-wrap items-center gap-2 sm:gap-4 text-xs text-muted">
      <span>{report.track_count} tracks</span>
      <span>·</span>
      <span>{report.nodes_executed.length} stages</span>
      {processingMs && <><span>·</span><span>{(processingMs / 1000).toFixed(1)}s</span></>}
      <span className="px-2 py-0.5 rounded-full border border-border uppercase tracking-wide">{report.tier}</span>
    </div>
  );
}

function MetricsRings({ metrics, maxPlays }: { metrics: NonNullable<Report["metrics"]>; maxPlays: number }) {
  return (
    <div className="rounded-xl border border-border bg-surface p-5 sm:p-6 card-lift">
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-6 justify-items-center stagger-children">
        <ProgressRing value={metrics.total_plays} max={maxPlays} color="var(--accent)" label="Total Plays" size={88} />
        <ProgressRing value={metrics.total_likes} max={maxPlays} color="var(--sky)" label="Total Likes" size={88} />
        <ProgressRing value={metrics.total_comments} max={maxPlays} color="var(--violet)" label="Comments" size={88} />
        <ProgressRing value={metrics.avg_engagement_rate * 100} max={100} color="var(--lime)" label="Engagement" size={88} suffix="%" decimals={1} />
      </div>
    </div>
  );
}

function EraTimeline({ eras, fingerprint }: { eras: NonNullable<Report["eras"]>; fingerprint?: Report["era_fingerprint"] }) {
  const maxEng = Math.max(...eras.map(e => e.avg_engagement_rate));
  return (
    <div className="space-y-3">
      <h2 className="text-lg font-semibold">Creative Eras</h2>
      <div className="flex gap-3 overflow-x-auto pb-2 -mx-4 px-4 sm:mx-0 sm:px-0">
        {eras.map((era) => {
          const best = fingerprint && era.avg_engagement_rate === maxEng;
          return (
            <div key={era.era_id} className={`flex-shrink-0 w-48 rounded-xl border bg-surface p-4 space-y-2 card-lift ${best ? "border-accent ring-1 ring-accent/20" : "border-border"}`}>
              <div className="flex items-center justify-between">
                <span className="text-sm font-semibold">{era.era_id}</span>
                {best && <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-accent/10 text-accent">Best</span>}
              </div>
              <div className="space-y-1 text-xs text-muted">
                <div className="flex justify-between"><span>Tracks</span><span className="font-mono">{era.track_count}</span></div>
                <div className="flex justify-between"><span>Plays</span><span className="font-mono">{era.total_plays.toLocaleString()}</span></div>
                <div className="flex justify-between"><span>Engagement</span><span className="font-mono">{(era.avg_engagement_rate * 100).toFixed(1)}%</span></div>
              </div>
              <p className="text-[10px] text-muted truncate">Top: {era.top_track}</p>
            </div>
          );
        })}
      </div>
    </div>
  );
}

const FP_CARDS = [
  { key: "genre", label: "Genre", border: "border-accent/20", bg: "bg-accent/[0.03]" },
  { key: "duration", label: "Avg Duration", border: "border-sky/20", bg: "bg-sky-dim" },
  { key: "plays", label: "Avg Plays", border: "border-violet/20", bg: "bg-violet-dim" },
  { key: "engagement", label: "Engagement", border: "border-lime/20", bg: "bg-lime-dim" },
] as const;

function EraFingerprint({ fp }: { fp: NonNullable<Report["era_fingerprint"]> }) {
  const values: Record<string, string> = {
    genre: fp.dominant_genre || "Mixed",
    duration: `${Math.round(fp.avg_duration_ms / 1000)}s`,
    plays: Math.round(fp.avg_plays).toLocaleString(),
    engagement: `${(fp.avg_engagement * 100).toFixed(1)}%`,
  };
  return (
    <div className="space-y-3">
      <h2 className="text-lg font-semibold">Strongest Era Fingerprint</h2>
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 stagger-children">
        {FP_CARDS.map((c) => (
          <div key={c.key} className={`rounded-xl border ${c.border} ${c.bg} p-3 space-y-1 card-lift`}>
            <p className="text-[10px] text-muted uppercase tracking-wide">{c.label}</p>
            <p className="text-sm font-semibold font-mono">{values[c.key]}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

function buildDayData(bestDay: string | null | undefined) {
  const days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];
  return days.map((day) => ({
    day,
    engagement: day === bestDay ? 1.0 : Math.random() * 0.5 + 0.1,
    count: day === bestDay ? 3 : Math.floor(Math.random() * 2),
  }));
}

function LoadingSkeleton() {
  return (
    <div className="space-y-6 stagger-children">
      <div className="rounded-xl border border-border bg-surface p-6 animate-pulse">
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-6 justify-items-center">
          {[...Array(4)].map((_, i) => <div key={i} className="w-[88px] h-[88px] rounded-full bg-border/50" />)}
        </div>
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        {[...Array(2)].map((_, i) => <div key={i} className="rounded-xl border border-border bg-surface p-5 space-y-2 animate-pulse"><div className="h-4 w-32 bg-border rounded" /><div className="h-3 w-48 bg-border rounded" /></div>)}
      </div>
    </div>
  );
}

function ErrorState({ message, onRetry }: { message: string; onRetry: () => void }) {
  return (
    <div className="rounded-xl border border-border bg-surface p-8 text-center space-y-4">
      <p className="text-muted">{message}</p>
      <button onClick={onRetry} className="px-4 py-2 bg-accent hover:bg-accent-hover text-white rounded-xl text-sm">Retry</button>
    </div>
  );
}
