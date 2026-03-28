"use client";

import type { Trends } from "../types";

export function GrowthVelocity({ trends }: { trends: Trends }) {
  const gv7 = trends.growth_velocity_7d ?? 0;
  const gv30 = trends.growth_velocity_30d ?? 0;
  const gv90 = trends.growth_velocity_90d ?? 0;
  const accelerating = trends.growth_accelerating ?? false;

  // Don't render if no growth data
  if (gv7 === 0 && gv30 === 0 && gv90 === 0) return null;

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2">
        <h2 className="text-lg font-semibold">Growth Velocity</h2>
        <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-violet-dim text-violet uppercase tracking-wider">Pro</span>
        {accelerating && <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-lime-dim text-lime">Accelerating</span>}
      </div>
      <div className="grid grid-cols-3 gap-3">
        <VelocityCard label="7 days" value={gv7} />
        <VelocityCard label="30 days" value={gv30} />
        <VelocityCard label="90 days" value={gv90} />
      </div>
    </div>
  );
}

function VelocityCard({ label, value }: { label: string; value: number }) {
  const pct = (value * 100).toFixed(1);
  const positive = value > 0;
  const color = positive ? "text-lime" : value < 0 ? "text-rose" : "text-muted";
  const arrow = positive ? "↑" : value < 0 ? "↓" : "→";
  const borderColor = positive ? "border-lime/20" : value < 0 ? "border-rose/20" : "border-border";
  const bgColor = positive ? "bg-lime-dim" : value < 0 ? "bg-rose-dim" : "bg-surface";

  return (
    <div className={`rounded-xl border ${borderColor} ${bgColor} p-3 sm:p-4 text-center space-y-1 card-lift`}>
      <p className="text-[10px] text-muted uppercase tracking-wide">{label}</p>
      <p className={`text-lg sm:text-xl font-bold font-mono tabular-nums ${color}`}>
        {arrow} {pct}%
      </p>
    </div>
  );
}
