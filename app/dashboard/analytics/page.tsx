"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

interface AnalyticsData {
  total_plays?: number;
  total_likes?: number;
  total_comments?: number;
  avg_engagement_rate?: number;
  top_tracks?: Array<{
    title: string;
    play_count: number;
    engagement_rate: number;
  }>;
}

export default function Analytics() {
  const [data, setData] = useState<AnalyticsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();

  useEffect(() => {
    // TODO: Wire to backend GET /analytics once pipeline is connected
    // For now, show the skeleton with placeholder state
    const timer = setTimeout(() => {
      setLoading(false);
      setError("Analytics pipeline not connected yet");
    }, 500);
    return () => clearTimeout(timer);
  }, []);

  return (
    <div className="min-h-screen">
      {/* Nav */}
      <nav className="border-b border-border px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <a href="/dashboard" className="text-lg font-bold hover:opacity-80">
            Cyba<span className="text-accent">Op</span>
          </a>
          <span className="text-xs text-muted">/ analytics</span>
        </div>
        <a
          href="/dashboard"
          className="text-sm text-muted hover:text-foreground"
        >
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
          <div className="rounded-lg border border-border bg-surface p-8 text-center space-y-4">
            <p className="text-muted">{error}</p>
            <p className="text-xs text-muted">
              The LangGraph analytics pipeline needs to be connected to the
              backend. Start Postgres and the FastAPI server to enable this.
            </p>
          </div>
        ) : (
          <AnalyticsGrid data={data!} />
        )}
      </div>
    </div>
  );
}

function LoadingSkeleton() {
  return (
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
  );
}

function AnalyticsGrid({ data }: { data: AnalyticsData }) {
  return (
    <div className="space-y-8">
      {/* Aggregate stats */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <StatCard label="Total Plays" value={data.total_plays} />
        <StatCard label="Total Likes" value={data.total_likes} />
        <StatCard label="Total Comments" value={data.total_comments} />
        <StatCard
          label="Avg Engagement"
          value={
            data.avg_engagement_rate
              ? `${(data.avg_engagement_rate * 100).toFixed(1)}%`
              : undefined
          }
        />
      </div>

      {/* Top tracks */}
      {data.top_tracks && data.top_tracks.length > 0 && (
        <div className="space-y-3">
          <h2 className="text-lg font-semibold">Top Tracks</h2>
          <div className="rounded-lg border border-border overflow-hidden">
            {data.top_tracks.map((track, i) => (
              <div
                key={i}
                className="flex items-center justify-between px-4 py-3 border-b border-border last:border-0 bg-surface"
              >
                <div className="flex items-center gap-3">
                  <span className="text-xs text-muted font-mono w-6">
                    {i + 1}
                  </span>
                  <span className="text-sm">{track.title}</span>
                </div>
                <div className="flex items-center gap-6 text-xs text-muted">
                  <span>{track.play_count.toLocaleString()} plays</span>
                  <span>
                    {(track.engagement_rate * 100).toFixed(1)}% engagement
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function StatCard({
  label,
  value,
}: {
  label: string;
  value?: number | string;
}) {
  return (
    <div className="rounded-lg border border-border bg-surface p-4 space-y-1">
      <p className="text-xs text-muted uppercase tracking-wide">{label}</p>
      <p className="text-2xl font-bold font-mono">
        {value !== undefined ? value.toLocaleString() : "—"}
      </p>
    </div>
  );
}
