"use client";

import { useState, useEffect } from "react";
import { CountUp } from "./count-up";

interface OnboardingProps {
  highlightStat?: number;
  highlightLabel?: string;
  onComplete: () => void;
}

export function Onboarding({ highlightStat, highlightLabel, onComplete }: OnboardingProps) {
  const [step, setStep] = useState(0);
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    if (step === 0) {
      const start = Date.now();
      const tick = () => {
        const elapsed = Date.now() - start;
        const pct = Math.min(elapsed / 2000, 1);
        setProgress(pct * 100);
        if (pct < 1) requestAnimationFrame(tick);
        else setTimeout(() => setStep(1), 300);
      };
      requestAnimationFrame(tick);
    }
  }, [step]);

  function handleComplete() {
    if (typeof window !== "undefined") {
      localStorage.setItem("cybaop_onboarded", "true");
    }
    onComplete();
  }

  return (
    <div className="fixed inset-0 z-[100] bg-black/85 backdrop-blur-sm flex items-center justify-center px-6">
      <button onClick={handleComplete} className="absolute top-6 right-6 text-xs text-muted hover:text-foreground">Skip</button>

      <div className="max-w-sm w-full space-y-6 text-center">
        {step === 0 && (
          <div className="space-y-4 animate-fade-in">
            <p className="text-lg font-semibold">Analyzing your catalog...</p>
            <div className="w-full h-2 bg-border rounded-full overflow-hidden">
              <div className="h-full bg-accent rounded-full" style={{ width: `${progress}%`, transition: "width 50ms linear" }} />
            </div>
            <p className="text-xs text-muted">Fetching tracks, computing metrics</p>
          </div>
        )}

        {step === 1 && (
          <div className="space-y-6 animate-fade-in">
            <p className="text-lg font-semibold">Here&apos;s what we found</p>
            {highlightStat !== undefined && (
              <div className="space-y-1">
                <p className="text-5xl font-black font-mono tabular-nums text-accent">
                  <CountUp end={highlightStat} />
                </p>
                <p className="text-sm text-muted">{highlightLabel || "total plays across your catalog"}</p>
              </div>
            )}
            <button onClick={() => setStep(2)} className="px-6 py-2 bg-surface border border-border rounded-lg text-sm hover:bg-surface-hover">Next</button>
          </div>
        )}

        {step === 2 && (
          <div className="space-y-6 animate-fade-in">
            <p className="text-lg font-semibold">Your dashboard is ready</p>
            <p className="text-sm text-muted">Explore your analytics, track performance, and release insights.</p>
            <button onClick={handleComplete} className="px-8 py-3 bg-accent hover:bg-accent-hover text-white font-semibold rounded-xl text-lg">Explore</button>
          </div>
        )}
      </div>
    </div>
  );
}
