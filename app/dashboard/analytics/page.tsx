"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";

interface TrackMetric {
  track_id: string;
  title: string;
  engagement_rate: number;
  performance_score: number;
  play_count?: number;
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
    } | null;
    trends?: unknown | null;
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
        if (res.status === 401) {
          router.push("/?error=auth_failed");
          return null;
        }
        return res.json();
      })
      .then((json) => {
        if (!json) return;
        if (json.success === false) {
          setError(json.message || "Failed to load analytics");
        } else {
          setData(json);
        }
        setLoading(false);
      })
      .catch(() => {
        setError("Failed to connect to analytics service");
        setLoading(false);
      });
  }, [router]);

  useEffect(() => {
    fetchAnalytics();
  }, [fetchAnalytics]);

  return (
    <div className="min-h-screen">
      <nav className="border-b border-border px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <a href="/dashboard" className="text-lg font-bold hover:opacity-80">
            Cyba<span className="text-accent">Op</span>
          </a>
          <span className="text-xs text-muted">/ analytics</span>
        </div>
        <a href="/dashboard" className="text-sm text-muted hover:text-foreground">
          ← Back to dashboard
        </a>
      </nav>

      <div className="max-w-5xl mx-auto px-6 py-10 space-y-8">
        <div>
          <h1 className="text-2xl font-bold">Analytics</h1>
          <p className="text-muted text-sm mt-1">
            Track performance, engagement trends, and catalog insights
          </p>
        </div>

        {loading ? (
          <LoadingSkeleton />
        ) : error ? (
          <ErrorState message={error} onRetry={fetchAnalytics} />
        ) : data?.report ? (
          <AnalyticsContent report={data.report} processingMs={data.processing_time_ms} />
        ) : (
          <ErrorState message="No data available" onRetry={fetchAnalytics} />
        )}
      </div>
    </div>
  );
}

function AnalyticsContent({
  report,
  processingMs,
}: {
  report: NonNullable<AnalyticsData["report"]>;
  processingMs?: number;
}) {
  const hasMetrics = report.metrics != null;

  return (
    <div className="space-y-8">
      {/* Processing info */}
      <div className="flex items-center gap-4 text-xs text-muted">
        <span>{report.track_count} tracks analyzed</span>
        <span>·</span>
        <span>{report.nodes_executed.length} pipeline stages</span>
        {processingMs && (
          <>
            <span>·</span>
            <span>{(processingMs / 1000).toFixed(1)}s</span>
          </>
        )}
        <span className="px-2 py-0.5 rounded-full border border-border uppercase tracking-wide">
          {report.tier}
        </span>
      </div>

      {/* Metrics grid (only if available — pro tier) */}
      {hasMetrics ? (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <StatCard label="Total Plays" value={report.metrics!.total_plays} />
          <StatCard label="Total Likes" value={report.metrics!.total_likes} />
          <StatCard label="Total Comments" value={report.metrics!.total_comments} />
          <StatCard
            label="Avg Engagement"
            value={`${(report.metrics!.avg_engagement_rate * 100).toFixed(1)}%`}
          />
        </div>
      ) : (
        <div className="rounded-lg border border-border bg-surface p-6 text-center space-y-2">
          <p className="text-sm text-muted">
            Detailed metrics are available on the Pro tier
          </p>
          <p className="text-xs text-muted">
            Upgrade to Pro for engagement rates, trend detection, and AI-powered insights
          </p>
        </div>
      )}

      {/* Top tracks */}
      {report.top_tracks && report.top_tracks.length > 0 && (
        <div className="space-y-3">
          <h2 className="text-lg font-semibold">Top Tracks</h2>
          <div className="rounded-lg border border-border overflow-hidden">
            {report.top_tracks.map((track, i) => (
              <div
                key={track.track_id}
                className="flex items-center justify-between px-4 py-3 border-b border-border last:border-0 bg-surface"
              >
                <div className="flex items-center gap-3">
                  <span className="text-xs text-muted font-mono w-6">{i + 1}</span>
                  <span className="text-sm">{track.title}</span>
                </div>
                <div className="flex items-center gap-6 text-xs text-muted">
                  {track.engagement_rate > 0 && (
                    <span>{(track.engagement_rate * 100).toFixed(1)}% engagement</span>
                  )}
                  {track.performance_score > 0 && (
                    <span>score: {track.performance_score.toFixed(1)}</span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function LoadingSkeleton() {
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        {[...Array(4)].map((_, i) => (
          <div
            key={i}
            className="rounded-lg border border-border bg-surface p-4 space-y-2 animate-pulse"
          >
            <div className="h-3 w-16 bg-border rounded" />
            <div className="h-8 w-24 bg-border rounded" />
          </div>
        ))}
      </div>
      <div className="rounded-lg border border-border bg-surface p-4 space-y-3 animate-pulse">
        {[...Array(5)].map((_, i) => (
          <div key={i} className="h-10 bg-border rounded" />
        ))}
      </div>
    </div>
  );
}

function ErrorState({ message, onRetry }: { message: string; onRetry: () => void }) {
  return (
    <div className="rounded-lg border border-border bg-surface p-8 text-center space-y-4">
      <p className="text-muted">{message}</p>
      <button
        onClick={onRetry}
        className="px-4 py-2 bg-accent hover:bg-accent-hover text-white rounded-lg text-sm transition-colors"
      >
        Retry
      </button>
    </div>
  );
}

function StatCard({ label, value }: { label: string; value: number | string }) {
  const display = typeof value === "number" ? value.toLocaleString() : value;
  return (
    <div className="rounded-lg border border-border bg-surface p-4 space-y-1">
      <p className="text-xs text-muted uppercase tracking-wide">{label}</p>
      <p className="text-2xl font-bold font-mono">{display}</p>
    </div>
  );
}
