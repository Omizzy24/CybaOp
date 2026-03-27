"use client";

import type { TrackMetric } from "../types";

export function TrackTable({ tracks }: { tracks: TrackMetric[] }) {
  if (tracks.length === 0) return null;

  return (
    <div className="space-y-3">
      <h2 className="text-lg font-semibold">Track Performance</h2>
      <div className="rounded-xl border border-border overflow-x-auto">
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
            {tracks.map((t, i) => (
              <tr key={t.track_id} className={`border-b border-border last:border-0 ${t.is_outlier ? (t.outlier_direction === "over" ? "bg-lime/5" : "bg-rose/5") : "bg-surface"}`}>
                <td className="px-3 sm:px-4 py-3 text-xs text-muted font-mono">{i + 1}</td>
                <td className="px-3 sm:px-4 py-3 text-sm sticky left-0 bg-inherit">
                  <span className="truncate block max-w-[200px]">{t.title}</span>
                  {t.is_outlier && <span className={`text-xs ${t.outlier_direction === "over" ? "text-lime" : "text-rose"}`}>{t.outlier_direction === "over" ? "↑ outperforming" : "↓ underperforming"}</span>}
                </td>
                <td className="px-3 sm:px-4 py-3 text-xs text-muted text-right font-mono tabular-nums">{(t.engagement_rate * 100).toFixed(1)}%</td>
                <td className="px-3 sm:px-4 py-3 text-xs text-muted text-right font-mono tabular-nums">{t.performance_score.toFixed(2)}</td>
                <td className="px-3 sm:px-4 py-3 text-xs text-muted text-right font-mono tabular-nums">{(t.plays_percentile * 100).toFixed(0)}%</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
