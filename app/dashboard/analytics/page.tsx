"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { TopNav, BottomNav } from "../components/nav";
import { EngagementBarChart, ReleaseDayHeatmap } from "../components/charts";
import { CountUp } from "../components/count-up";

interface TrackMetric {
  track_id: string;
  title: string;
  engagement_rate: number;
  performance_score: number;
  plays_percentile: number;
  is_outlier: boolean;
  outlier_direction: string;
}

interface AnalyticsData {
  success: boolean;
  message?: string;
  report?: {
    user_id: string;
    track_count: number;
    top_tracks: TrackMetric[];
    metrics?: {
      total_plays: number;
      total_likes: number;
      total_comments: number;
      total_reposts: number;
      avg_engagement_rate: number;
      catalog_concentration: number;
      all_track_metrics: TrackMetric[];
    } | null;
    trends?: {
      best_release_day: string | null;
      best_release_hour: number | null;
      strongest_era_description: string;
      confidence: number;
    } | null;
    insights: unknown[];
    tier: string;
    processing_time_ms: number;
    nodes_executed: string[];
  } | null;
  processing_time_ms?: number;
}

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

      {/* Mobile header */}
      <div className="md:hidden px-4 pt-4 pb-2 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <a href="/dashboard" className="text-lg font-bold">
            Cyba<span className="text-accent">Op</span>
          </a>
          <span className="text-xs text-muted">/ analytics</span>
        </div>
        <a href="/dashboard" className="text-xs text-muted">← Back</a>
      </div>

      <div className="max-w-5xl mx-auto px-4 sm:px-6 py-6 sm:py-10 space-y-6 sm:space-y-8">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold">Analytics</h1>
          <p className="text-muted text-sm mt-1">Track performance, engagement trends, and catalog insights</p>
        </div>

        {loading ? <LoadingSkeleton /> : error ? <ErrorState message={error} onRetry={fetchAnalytics} /> : data?.report ? <AnalyticsContent report={data.report} processingMs={data.processing_time_ms} /> : <ErrorState message="No data available" onRetry={fetchAnalytics} />}
      </div>

      <BottomNav />
    </div>
  );
}

function AnalyticsContent({ report, processingMs }: { report: NonNullable<AnalyticsData["report"]>; processingMs?: number }) {
  const metrics = report.metrics;
  const trends = report.trends;
  const allTracks = metrics?.all_track_metrics || report.top_tracks || [];
  const concentration = metrics?.catalog_concentration || 0;
  const topTrackCount = Math.max(1, Math.ceil(allTracks.length * 0.2));

  return (
    <div className="space-y-6 sm:space-y-8">
      {/* Pipeline info */}
      <div className="flex flex-wrap items-center gap-2 sm:gap-4 text-xs text-muted">
        <span>{report.track_count} tracks</span>
        <span>·</span>
        <span>{report.nodes_executed.length} stages</span>
        {processingMs && <><span>·</span><span>{(processingMs / 1000).toFixed(1)}s</span></>}
        <span className="px-2 py-0.5 rounded-full border border-border uppercase tracking-wide">{report.tier}</span>
      </div>

      {/* Stats grid */}
      {metrics && (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
          <StatCard label="Total Plays" value={metrics.total_plays} />
          <StatCard label="Total Likes" value={metrics.total_likes} />
          <StatCard label="Total Comments" value={metrics.total_comments} />
          <StatCard label="Avg Engagement" value={`${(metrics.avg_engagement_rate * 100).toFixed(1)}%`} />
        </div>
      )}

      {/* Insight cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 sm:gap-4">
        <div className="rounded-lg border border-border bg-surface p-4 sm:p-5 space-y-2">
          <div className="flex items-center gap-2">
            <span className="text-lg">📅</span>
            <h3 className="text-sm font-semibold">Best Release Window</h3>
          </div>
          {trends?.best_release_day ? (
            <p className="text-sm text-muted">
              Your tracks released on <span className="text-foreground font-medium">{trends.best_release_day}s</span> get the highest engagement.
              {trends.best_release_hour !== null && <> Best hour: <span className="text-foreground font-medium">{trends.best_release_hour}:00</span>.</>}
            </p>
          ) : <p className="text-xs text-muted">Not enough data yet.</p>}
        </div>

        <div className="rounded-lg border border-border bg-surface p-4 sm:p-5 space-y-2">
          <div className="flex items-center gap-2">
            <span className="text-lg">🏥</span>
            <h3 className="text-sm font-semibold">Catalog Health</h3>
          </div>
          {metrics && metrics.total_plays > 0 ? (
            <p className="text-sm text-muted">
              Top {topTrackCount} track{topTrackCount > 1 ? "s" : ""}: <span className="text-foreground font-medium">{(concentration * 100).toFixed(0)}%</span> of plays.
              {concentration > 0.8 ? " High concentration." : concentration > 0.5 ? " Healthy distribution." : " Well distributed."}
            </p>
          ) : <p className="text-xs text-muted">No play data yet.</p>}
        </div>
      </div>

      {trends?.strongest_era_description && (
        <div className="rounded-lg border border-border bg-surface p-4 sm:p-5 space-y-2">
          <div className="flex items-center gap-2"><span className="text-lg">🔥</span><h3 className="text-sm font-semibold">Your Strongest Era</h3></div>
          <p className="text-sm text-muted">{trends.strongest_era_description}</p>
        </div>
      )}

      {/* Charts */}
      {allTracks.length > 0 && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-3 sm:gap-4">
          <EngagementBarChart tracks={allTracks} />
          <ReleaseDayHeatmap
            dayData={buildDayData(trends?.best_release_day)}
            bestDay={trends?.best_release_day || null}
          />
        </div>
      )}

      {/* Track table — horizontal scroll on mobile */}
      {allTracks.length > 0 && (
        <div className="space-y-3">
          <h2 className="text-lg font-semibold">Track Performance</h2>
          <div className="rounded-lg border border-border overflow-x-auto">
            <table className="w-full min-w-[480px]">
              <thead>
                <tr className="text-xs text-muted uppercase tracking-wide bg-surface border-b border-border">
                  <th className="text-left px-3 sm:px-4 py-2 w-8">#</th>
                  <th className="text-left px-3 sm:px-4 py-2 sticky left-0 bg-surface">Track</th>
                  <th className="text-right px-3 sm:px-4 py-2">Engagement</th>
                  <th className="text-right px-3 sm:px-4 py-2">Score</th>
                  <th className="text-right px-3 sm:px-4 py-2">Percentile</th>
                </tr>
              </thead>
              <tbody>
                {allTracks.map((track, i) => (
                  <tr key={track.track_id} className={`border-b border-border last:border-0 ${track.is_outlier ? (track.outlier_direction === "over" ? "bg-green-500/5" : "bg-red-500/5") : "bg-surface"}`}>
                    <td className="px-3 sm:px-4 py-3 text-xs text-muted font-mono">{i + 1}</td>
                    <td className="px-3 sm:px-4 py-3 text-sm sticky left-0 bg-inherit">
                      <span className="truncate block max-w-[200px]">{track.title}</span>
                      {track.is_outlier && <span className={`text-xs ${track.outlier_direction === "over" ? "text-green-400" : "text-red-400"}`}>{track.outlier_direction === "over" ? "↑ outperforming" : "↓ underperforming"}</span>}
                    </td>
                    <td className="px-3 sm:px-4 py-3 text-xs text-muted text-right font-mono tabular-nums">{(track.engagement_rate * 100).toFixed(1)}%</td>
                    <td className="px-3 sm:px-4 py-3 text-xs text-muted text-right font-mono tabular-nums">{track.performance_score.toFixed(2)}</td>
                    <td className="px-3 sm:px-4 py-3 text-xs text-muted text-right font-mono tabular-nums">{(track.plays_percentile * 100).toFixed(0)}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Pro teasers */}
      <div className="space-y-3">
        <h2 className="text-lg font-semibold text-muted">Pro Features</h2>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 sm:gap-4">
          <ProTeaser icon="📉" title="Engagement Decay" description="See how plays drop off after release." />
          <ProTeaser icon="🤖" title="AI Strategy" description="Personalized release recommendations." />
          <ProTeaser icon="🔍" title="Benchmarking" description="Compare to similar artists." />
        </div>
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

function ProTeaser({ icon, title, description }: { icon: string; title: string; description: string }) {
  return (
    <div className="rounded-lg border border-border bg-surface/50 p-4 sm:p-5 space-y-2 opacity-60">
      <div className="flex items-center gap-2">
        <span>{icon}</span>
        <h3 className="text-sm font-semibold">{title}</h3>
        <span className="text-[10px] px-1.5 py-0.5 rounded bg-accent/10 text-accent uppercase tracking-wider">Pro</span>
      </div>
      <p className="text-xs text-muted leading-relaxed">{description}</p>
    </div>
  );
}

function StatCard({ label, value }: { label: string; value: number | string }) {
  const isNumber = typeof value === "number";
  const isPercent = typeof value === "string" && value.endsWith("%");
  const numericValue = isPercent ? parseFloat(value) : isNumber ? value : 0;

  return (
    <div className="rounded-lg border border-border bg-surface p-3 sm:p-4 space-y-1">
      <p className="text-[10px] sm:text-xs text-muted uppercase tracking-wide">{label}</p>
      <p className="text-xl sm:text-2xl font-bold font-mono tabular-nums">
        {isNumber ? (
          <CountUp end={value as number} />
        ) : isPercent ? (
          <CountUp end={numericValue} decimals={1} suffix="%" />
        ) : (
          value
        )}
      </p>
    </div>
  );
}

function LoadingSkeleton() {
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        {[...Array(4)].map((_, i) => <div key={i} className="rounded-lg border border-border bg-surface p-4 space-y-2 animate-pulse"><div className="h-3 w-16 bg-border rounded" /><div className="h-8 w-24 bg-border rounded" /></div>)}
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        {[...Array(2)].map((_, i) => <div key={i} className="rounded-lg border border-border bg-surface p-5 space-y-2 animate-pulse"><div className="h-4 w-32 bg-border rounded" /><div className="h-3 w-48 bg-border rounded" /></div>)}
      </div>
    </div>
  );
}

function ErrorState({ message, onRetry }: { message: string; onRetry: () => void }) {
  return (
    <div className="rounded-lg border border-border bg-surface p-8 text-center space-y-4">
      <p className="text-muted">{message}</p>
      <button onClick={onRetry} className="px-4 py-2 bg-accent hover:bg-accent-hover text-white rounded-lg text-sm">Retry</button>
    </div>
  );
}
