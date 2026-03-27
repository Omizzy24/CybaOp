"use client";
import { useSearchParams } from "next/navigation";
import { Suspense } from "react";

const ERRORS: Record<string, string> = {
  auth_failed: "Authentication failed — please try again.",
  timeout: "The server took too long to respond.",
  service_unavailable: "Authentication service is temporarily unavailable.",
  exchange_failed: "Something went wrong during sign-in.",
};

function HomeContent() {
  const params = useSearchParams();
  const error = params.get("error");

  return (
    <main className="min-h-screen bg-[#050505] text-foreground overflow-hidden">
      <div className="fixed inset-0 -z-10">
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,rgba(249,115,22,0.03)_0%,transparent_70%)]" />
      </div>

      <section className="min-h-screen flex flex-col items-center justify-center px-6 py-20">
        <div className="max-w-3xl text-center space-y-8">
          <div className="space-y-4">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-white/10 text-xs text-muted tracking-wide uppercase">
              <span className="w-1.5 h-1.5 rounded-full bg-accent animate-pulse" />
              Beta
            </div>
            <h1 className="text-6xl sm:text-7xl lg:text-8xl font-black tracking-tight">
              Cyba<span className="text-accent">Op</span>
            </h1>
            <p className="text-lg sm:text-xl text-muted max-w-xl mx-auto leading-relaxed">
              The intelligence layer for SoundCloud creators. Know what works. Know when to release.
            </p>
          </div>

          <p className="text-xs text-muted/60">Join 500+ SoundCloud creators</p>

          {error && (
            <div className="mx-auto max-w-md px-4 py-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-sm">
              {ERRORS[error] || "An unexpected error occurred."}
            </div>
          )}

          <div className="flex flex-col items-center gap-3">
            <a href="/api/auth/soundcloud" className="inline-flex items-center gap-2 px-8 py-4 bg-accent hover:bg-accent-hover text-white font-semibold rounded-xl text-lg animate-cta-pulse">
              Connect SoundCloud
            </a>
            <p className="text-[11px] text-muted/50">Read-only access. We never modify your account.</p>
          </div>
        </div>
      </section>

      <section className="px-6 py-20">
        <div className="max-w-4xl mx-auto space-y-10">
          <div className="text-center space-y-2">
            <h2 className="text-2xl sm:text-3xl font-bold">Stop guessing. Start knowing.</h2>
            <p className="text-sm text-muted">SoundCloud gives you numbers. CybaOp gives you answers.</p>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
            <div className="rounded-2xl border border-white/5 bg-white/[0.02] backdrop-blur-xl p-6 space-y-4">
              <p className="text-xs text-muted uppercase tracking-wider">What SoundCloud shows you</p>
              <div className="space-y-3">
                <div className="flex justify-between text-sm"><span className="text-muted">Plays</span><span className="font-mono">2,847</span></div>
                <div className="flex justify-between text-sm"><span className="text-muted">Likes</span><span className="font-mono">42</span></div>
                <div className="flex justify-between text-sm"><span className="text-muted">Comments</span><span className="font-mono">15</span></div>
              </div>
              <p className="text-xs text-muted/50 italic">...and that&apos;s it.</p>
            </div>
            <div className="rounded-2xl border border-accent/20 bg-accent/[0.03] backdrop-blur-xl p-6 space-y-4 ring-1 ring-accent/10">
              <p className="text-xs text-accent uppercase tracking-wider">What CybaOp shows you</p>
              <div className="space-y-3">
                <div className="flex justify-between text-sm"><span className="text-muted">Engagement Rate</span><span className="font-mono text-accent">2.3%</span></div>
                <div className="flex justify-between text-sm"><span className="text-muted">Best Release Day</span><span className="font-mono text-accent">Thursday</span></div>
                <div className="flex justify-between text-sm"><span className="text-muted">Top Track</span><span className="font-mono text-green-400">outperforming</span></div>
                <div className="flex justify-between text-sm"><span className="text-muted">Catalog Health</span><span className="font-mono text-accent">72%</span></div>
              </div>
              <p className="text-xs text-accent/60 italic">Actionable intelligence, not just numbers.</p>
            </div>
          </div>
        </div>
      </section>

      <section className="px-6 py-20">
        <div className="max-w-4xl mx-auto grid grid-cols-1 sm:grid-cols-3 gap-4 sm:gap-6">
          <div className="p-5 rounded-xl border border-white/5 bg-white/[0.02] space-y-3">
            <span className="text-2xl">📊</span>
            <h3 className="text-sm font-semibold">Track Analytics</h3>
            <p className="text-xs text-muted leading-relaxed">Engagement rates, performance scores, outlier detection, and catalog concentration.</p>
          </div>
          <div className="p-5 rounded-xl border border-white/5 bg-white/[0.02] space-y-3">
            <span className="text-2xl">📈</span>
            <h3 className="text-sm font-semibold">Trend Detection</h3>
            <p className="text-xs text-muted leading-relaxed">Best release timing, strongest era analysis, and growth velocity.</p>
          </div>
          <div className="p-5 rounded-xl border border-white/5 bg-white/[0.02] space-y-3">
            <span className="text-2xl">🧠</span>
            <h3 className="text-sm font-semibold">AI Insights</h3>
            <p className="text-xs text-muted leading-relaxed">Personalized recommendations powered by your catalog data.</p>
          </div>
        </div>
      </section>

      <footer className="px-6 py-10 border-t border-white/5">
        <div className="max-w-4xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-muted/40">
          <span>CybaOp 2026</span>
          <span>Built for SoundCloud creators</span>
        </div>
      </footer>
    </main>
  );
}

export default function Home() {
  return <Suspense><HomeContent /></Suspense>;
}
