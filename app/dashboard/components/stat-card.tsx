"use client";

import { CountUp } from "./count-up";

interface StatCardProps {
  label: string;
  value: number | string;
  accent?: string;
}

export function StatCard({ label, value, accent }: StatCardProps) {
  const isNumber = typeof value === "number";
  const isPercent = typeof value === "string" && value.endsWith("%");
  const numericValue = isPercent ? parseFloat(value) : isNumber ? value : 0;

  return (
    <div
      className="rounded-xl border border-border bg-surface p-3 sm:p-4 space-y-1 card-lift"
      style={accent ? { borderColor: `color-mix(in srgb, ${accent} 25%, transparent)` } : undefined}
    >
      <p className="text-[10px] sm:text-xs text-muted uppercase tracking-wide">{label}</p>
      <p className="text-xl sm:text-2xl font-bold font-mono tabular-nums">
        {isNumber ? <CountUp end={value as number} /> : isPercent ? <CountUp end={numericValue} decimals={1} suffix="%" /> : value}
      </p>
    </div>
  );
}
