"use client";

interface CritiquePanelProps {
  critique: {
    strength: string;
    weakness: string;
    diagnosis: string;
    recommendation: string;
  };
  trackTitle?: string;
}

const SECTIONS = [
  { key: "strength", label: "Strength", color: "text-lime" },
  { key: "weakness", label: "Weakness", color: "text-rose" },
  { key: "diagnosis", label: "Diagnosis", color: "text-amber" },
  { key: "recommendation", label: "Recommendation", color: "text-sky" },
] as const;

export function CritiquePanel({ critique, trackTitle }: CritiquePanelProps) {
  return (
    <div className="rounded-xl border border-border bg-surface p-4 sm:p-5 space-y-4">
      {trackTitle && (
        <p className="text-sm font-mono font-semibold truncate">{trackTitle}</p>
      )}

      {SECTIONS.map(({ key, label, color }) => (
        <div key={key} className="space-y-1">
          <p className={`text-[10px] font-mono uppercase tracking-wider ${color}`}>
            {label}
          </p>
          <p className="text-sm font-mono text-foreground leading-relaxed">
            {critique[key]}
          </p>
        </div>
      ))}
    </div>
  );
}
