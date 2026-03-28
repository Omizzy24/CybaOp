"use client";

import type { HealthScorePoint } from "@/app/dashboard/types";

interface HealthScoreDisplayProps {
  score: number | null;
  history?: HealthScorePoint[];
  missingComponents?: string[];
}

function getScoreColor(score: number): string {
  if (score <= 33) return "text-rose";
  if (score <= 66) return "text-amber";
  return "text-lime";
}

function Sparkline({ points }: { points: number[] }) {
  if (points.length < 2) return null;

  const width = 120;
  const height = 32;
  const padding = 2;

  const min = Math.min(...points);
  const max = Math.max(...points);
  const range = max - min || 1;

  const coords = points.map((val, i) => {
    const x = padding + (i / (points.length - 1)) * (width - padding * 2);
    const y = height - padding - ((val - min) / range) * (height - padding * 2);
    return `${x},${y}`;
  });

  return (
    <svg
      width={width}
      height={height}
      viewBox={`0 0 ${width} ${height}`}
      className="inline-block"
      aria-hidden="true"
    >
      <polyline
        points={coords.join(" ")}
        fill="none"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
        className="text-muted"
      />
    </svg>
  );
}

export function HealthScoreDisplay({ score, history, missingComponents }: HealthScoreDisplayProps) {
  const last10 = (history ?? []).slice(-10).map((p) => p.score);

  return (
    <div className="space-y-3">
      <div className="flex items-end gap-4">
        <span
          className={`text-5xl font-mono font-bold tabular-nums ${score !== null ? getScoreColor(score) : "text-muted"}`}
        >
          {score !== null ? score : "—"}
        </span>
        {last10.length >= 2 && <Sparkline points={last10} />}
      </div>

      {missingComponents && missingComponents.length > 0 && (
        <p className="text-xs text-muted font-mono">
          Missing: {missingComponents.join(", ")}
        </p>
      )}
    </div>
  );
}
