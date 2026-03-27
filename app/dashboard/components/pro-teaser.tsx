"use client";

import { useEffect, useState } from "react";

interface ProTeaserProps {
  icon: string;
  title: string;
  description: string;
  featureId: string;
}

export function ProTeaser({ icon, title, description, featureId }: ProTeaserProps) {
  const [mode, setMode] = useState<"idle" | "input" | "done">("idle");
  const [email, setEmail] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    if (typeof window === "undefined") return;
    try {
      const stored = JSON.parse(localStorage.getItem("cybaop_pro_waitlist") || "[]");
      if (stored.some((e: any) => e.feature === featureId)) setMode("done");
    } catch {}
  }, [featureId]);

  function handleSubmit() {
    setError("");
    if (!email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) { setError("Enter a valid email"); return; }
    if (typeof window === "undefined") return;
    try {
      const stored = JSON.parse(localStorage.getItem("cybaop_pro_waitlist") || "[]");
      stored.push({ email, feature: featureId, timestamp: new Date().toISOString() });
      localStorage.setItem("cybaop_pro_waitlist", JSON.stringify(stored));
      setMode("done");
    } catch {}
  }

  return (
    <div className="rounded-xl border border-border bg-surface/50 p-4 sm:p-5 space-y-3 card-lift">
      <div className="flex items-center gap-2">
        <span>{icon}</span>
        <h3 className="text-sm font-semibold">{title}</h3>
        <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-violet-dim text-violet uppercase tracking-wider">Pro</span>
      </div>
      <p className="text-xs text-muted leading-relaxed">{description}</p>
      {mode === "idle" && (
        <button onClick={() => setMode("input")} className="text-xs text-accent hover:text-accent-hover font-medium">Notify me when available →</button>
      )}
      {mode === "input" && (
        <div className="space-y-1.5">
          <div className="flex gap-2">
            <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} onKeyDown={(e) => e.key === "Enter" && handleSubmit()} placeholder="your@email.com" className="flex-1 min-w-0 px-2.5 py-1.5 text-xs bg-background border border-border rounded-md focus:border-accent focus:outline-none" />
            <button onClick={handleSubmit} disabled={!email} className="px-3 py-1.5 text-xs bg-accent text-white rounded-md disabled:opacity-40">Submit</button>
          </div>
          {error && <p className="text-[10px] text-rose">{error}</p>}
        </div>
      )}
      {mode === "done" && <p className="text-xs text-lime flex items-center gap-1">✓ You&apos;re on the list</p>}
    </div>
  );
}
