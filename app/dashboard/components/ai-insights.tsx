"use client";

import type { Insight } from "../types";

const CATEGORY_STYLES: Record<string, { icon: string; border: string; bg: string }> = {
  performance: { icon: "🎯", border: "border-accent/20", bg: "bg-accent/[0.03]" },
  timing: { icon: "⏰", border: "border-sky/20", bg: "bg-sky-dim" },
  catalog: { icon: "📀", border: "border-violet/20", bg: "bg-violet-dim" },
  growth: { icon: "📈", border: "border-lime/20", bg: "bg-lime-dim" },
};

export function AIInsights({ insights }: { insights: Insight[] }) {
  if (insights.length === 0) return null;

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2">
        <h2 className="text-lg font-semibold">AI Insights</h2>
        <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-violet-dim text-violet uppercase tracking-wider">Pro</span>
      </div>
      <div className="grid grid-cols-1 gap-3 stagger-children">
        {insights.map((insight, i) => {
          const style = CATEGORY_STYLES[insight.category] || CATEGORY_STYLES.performance;
          return (
            <div key={i} className={`rounded-xl border ${style.border} ${style.bg} p-4 sm:p-5 space-y-2 card-lift`}>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span>{style.icon}</span>
                  <h3 className="text-sm font-semibold">{insight.headline}</h3>
                </div>
                <div className="flex items-center gap-1.5">
                  {insight.actionable && <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-lime-dim text-lime">Actionable</span>}
                  <ConfidenceDots confidence={insight.confidence} />
                </div>
              </div>
              <p className="text-sm text-muted leading-relaxed">{insight.detail}</p>
              {insight.actionable && insight.recommendation && (
                <div className="flex items-start gap-2 pt-1">
                  <span className="text-xs text-accent">→</span>
                  <p className="text-xs text-accent">{insight.recommendation}</p>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

function ConfidenceDots({ confidence }: { confidence: number }) {
  const filled = Math.round(confidence * 5);
  return (
    <div className="flex gap-0.5" title={`${Math.round(confidence * 100)}% confidence`}>
      {Array.from({ length: 5 }).map((_, i) => (
        <span key={i} className="w-1 h-1 rounded-full" style={{ background: i < filled ? "var(--accent)" : "var(--border)" }} />
      ))}
    </div>
  );
}
