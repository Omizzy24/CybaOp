"use client";
import { useSearchParams, useRouter } from "next/navigation";
import { Suspense, useEffect, useState } from "react";

const ERRORS: Record<string, string> = {
  auth_failed: "Authentication failed — please try again.",
  timeout: "The server took too long to respond.",
  service_unavailable: "Authentication service is temporarily unavailable.",
  exchange_failed: "Something went wrong during sign-in.",
  unexpected: "An unexpected error occurred.",
};

function HomeContent() {
  const params = useSearchParams();
  const router = useRouter();
  const error = params.get("error");

  const [isCheckingAuth, setIsCheckingAuth] = useState(true);
  const [isConnecting, setIsConnecting] = useState(false);

  useEffect(() => {
    fetch("/api/auth/me")
      .then((res) => {
        if (res.status === 200) {
          router.push("/dashboard");
          return;
        }
        setIsCheckingAuth(false);
      })
      .catch(() => {
        setIsCheckingAuth(false);
      });
  }, [router]);

  function handleConnect() {
    setIsConnecting(true);
    window.location.href = "/api/auth/soundcloud";
  }

  if (isCheckingAuth) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#050505]">
        <div className="flex items-center gap-3 text-muted">
          <div className="w-5 h-5 border-2 border-muted border-t-accent rounded-full animate-spin" />
          Loading...
        </div>
      </div>
    );
  }

  return (
    <main className="min-h-screen bg-[#050505] text-foreground overflow-hidden">
      <div className="fixed inset-0 -z-10">
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,rgba(249,115,22,0.03)_0%,transparent_70%)]" />
      </div>

      {/* ===== HERO ===== */}
      <section className="min-h-screen flex flex-col items-center justify-center px-6 py-20 animate-page-enter">
        <div className="max-w-3xl text-center space-y-8">
          <div className="space-y-4">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-white/10 text-xs text-muted tracking-wide uppercase">
              <span className="w-1.5 h-1.5 rounded-full bg-accent animate-pulse" />
              Beta
            </div>
            <h1 className="text-5xl sm:text-6xl lg:text-8xl font-black tracking-tight">
              Cyba<span className="text-accent">Op</span>
            </h1>
            <p className="text-lg sm:text-xl text-muted max-w-xl mx-auto leading-relaxed">
              Analytics intelligence for SoundCloud creators. Engagement rates, trend detection, release timing, and AI-powered insights — all from your catalog data.
            </p>
          </div>

          <p className="text-xs text-muted/60">Built for independent SoundCloud artists</p>

          {error && (
            <div className="mx-auto max-w-md px-4 py-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-sm">
              <p>{ERRORS[error] || ERRORS.unexpected}</p>
              <a
                href="/api/auth/soundcloud"
                className="underline text-red-300 hover:text-red-200 text-xs mt-1 inline-block"
              >
                Try again →
              </a>
            </div>
          )}

          <div className="flex flex-col items-center gap-3">
            <button
              onClick={handleConnect}
              disabled={isConnecting}
              className="inline-flex items-center gap-2 px-8 py-4 bg-accent hover:bg-accent-hover text-white font-semibold rounded-xl text-lg animate-cta-pulse disabled:opacity-60 disabled:cursor-not-allowed min-h-[44px] min-w-[44px]"
            >
              {isConnecting ? (
                <>
                  <div className="w-4 h-4 border-2 border-white/40 border-t-white rounded-full animate-spin" />
                  Connecting...
                </>
              ) : (
                "Connect SoundCloud"
              )}
            </button>
            <p className="text-[11px] text-muted/50">Read-only access. We never modify your account.</p>
          </div>
        </div>
      </section>

      {/* ===== HOW IT WORKS ===== */}
      <section className="px-6 py-20">
        <div className="max-w-4xl mx-auto space-y-10 animate-page-enter">
          <div className="text-center space-y-2">
            <h2 className="text-2xl sm:text-3xl font-bold">How it works</h2>
            <p className="text-sm text-muted">Three steps to real analytics</p>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-6 stagger-children">
            <div className="text-center space-y-3 p-6">
              <div className="w-12 h-12 rounded-full bg-accent/10 border border-accent/20 flex items-center justify-center mx-auto">
                <span className="text-accent font-bold font-mono">1</span>
              </div>
              <h3 className="text-sm font-semibold">Connect</h3>
              <p className="text-xs text-muted leading-relaxed">Sign in with your SoundCloud account. Read-only — we never modify anything.</p>
            </div>
            <div className="text-center space-y-3 p-6">
              <div className="w-12 h-12 rounded-full bg-accent/10 border border-accent/20 flex items-center justify-center mx-auto">
                <span className="text-accent font-bold font-mono">2</span>
              </div>
              <h3 className="text-sm font-semibold">Analyze</h3>
              <p className="text-xs text-muted leading-relaxed">We crunch your catalog data — engagement rates, trends, outliers, and growth patterns.</p>
            </div>
            <div className="text-center space-y-3 p-6">
              <div className="w-12 h-12 rounded-full bg-accent/10 border border-accent/20 flex items-center justify-center mx-auto">
                <span className="text-accent font-bold font-mono">3</span>
              </div>
              <h3 className="text-sm font-semibold">Act</h3>
              <p className="text-xs text-muted leading-relaxed">Get actionable insights — best release timing, catalog health, and AI-powered recommendations.</p>
            </div>
          </div>
        </div>
      </section>

      {/* ===== FEATURE CARDS ===== */}
      <section className="px-6 py-20">
        <div className="max-w-4xl mx-auto space-y-10">
          <div className="text-center space-y-2">
            <h2 className="text-2xl sm:text-3xl font-bold">What you get</h2>
            <p className="text-sm text-muted">Beyond basic play counts</p>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6 stagger-children">
            <div className="p-5 rounded-2xl border border-white/5 bg-white/[0.02] space-y-3">
              <span className="text-2xl">📊</span>
              <h3 className="text-sm font-semibold">Track Analytics</h3>
              <p className="text-xs text-muted leading-relaxed">Engagement rates, performance scores, outlier detection across your entire catalog.</p>
            </div>
            <div className="p-5 rounded-2xl border border-white/5 bg-white/[0.02] space-y-3">
              <span className="text-2xl">📈</span>
              <h3 className="text-sm font-semibold">Trend Detection</h3>
              <p className="text-xs text-muted leading-relaxed">Best release timing, growth velocity, and strongest era analysis for your tracks.</p>
            </div>
            <div className="p-5 rounded-2xl border border-white/5 bg-white/[0.02] space-y-3">
              <span className="text-2xl">🧠</span>
              <h3 className="text-sm font-semibold">AI Insights</h3>
              <p className="text-xs text-muted leading-relaxed">Personalized recommendations powered by your catalog data and listening patterns.</p>
            </div>
            <div className="p-5 rounded-2xl border border-white/5 bg-white/[0.02] space-y-3">
              <span className="text-2xl">🚨</span>
              <h3 className="text-sm font-semibold">Catalog Triage</h3>
              <p className="text-xs text-muted leading-relaxed">Production health monitoring, incident detection, and remediation guidance.</p>
            </div>
            <div className="p-5 rounded-2xl border border-white/5 bg-white/[0.02] space-y-3">
              <span className="text-2xl">🔄</span>
              <h3 className="text-sm font-semibold">Creator Workflows</h3>
              <p className="text-xs text-muted leading-relaxed">Guided multi-step analysis sessions — portfolio critique, release planning, and more.</p>
            </div>
          </div>
        </div>
      </section>

      {/* ===== COMPARISON ===== */}
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

      {/* ===== TRUST SIGNALS ===== */}
      <section className="px-6 py-20">
        <div className="max-w-4xl mx-auto space-y-10">
          <div className="text-center space-y-2">
            <h2 className="text-2xl sm:text-3xl font-bold">Built for independent SoundCloud artists</h2>
            <p className="text-sm text-muted">Your data, your insights, no compromises</p>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 sm:gap-6 stagger-children">
            <div className="p-5 rounded-2xl border border-white/5 bg-white/[0.02] text-center space-y-3">
              <span className="text-2xl">🔒</span>
              <h3 className="text-sm font-semibold">Read-only access</h3>
              <p className="text-xs text-muted leading-relaxed">We only read your public profile and track data. We never post, delete, or modify anything.</p>
            </div>
            <div className="p-5 rounded-2xl border border-white/5 bg-white/[0.02] text-center space-y-3">
              <span className="text-2xl">🛡️</span>
              <h3 className="text-sm font-semibold">No data stored on third parties</h3>
              <p className="text-xs text-muted leading-relaxed">Your analytics stay between you and CybaOp. No third-party data sharing.</p>
            </div>
            <div className="p-5 rounded-2xl border border-white/5 bg-white/[0.02] text-center space-y-3">
              <span className="text-2xl">📖</span>
              <h3 className="text-sm font-semibold">Open analytics</h3>
              <p className="text-xs text-muted leading-relaxed">Transparent methodology. Every metric is explained so you understand what drives your numbers.</p>
            </div>
          </div>
        </div>
      </section>

      {/* ===== SECONDARY CTA ===== */}
      <section className="px-6 py-20">
        <div className="max-w-2xl mx-auto text-center space-y-6">
          <h2 className="text-2xl sm:text-3xl font-bold">Ready to see your real numbers?</h2>
          <p className="text-sm text-muted">Connect your SoundCloud and get insights in seconds.</p>
          <div className="flex flex-col items-center gap-3">
            <button
              onClick={handleConnect}
              disabled={isConnecting}
              className="inline-flex items-center gap-2 px-8 py-4 bg-accent hover:bg-accent-hover text-white font-semibold rounded-xl text-lg disabled:opacity-60 disabled:cursor-not-allowed min-h-[44px] min-w-[44px]"
            >
              {isConnecting ? (
                <>
                  <div className="w-4 h-4 border-2 border-white/40 border-t-white rounded-full animate-spin" />
                  Connecting...
                </>
              ) : (
                "Connect SoundCloud"
              )}
            </button>
            <p className="text-[11px] text-muted/50">Read-only access. We never modify your account.</p>
          </div>
        </div>
      </section>

      {/* ===== FOOTER ===== */}
      <footer className="px-6 py-10 border-t border-white/5">
        <div className="max-w-4xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-muted/40">
          <span>&copy; {new Date().getFullYear()} CybaOp</span>
          <span>Built for SoundCloud creators</span>
          <div className="flex items-center gap-4">
            <a href="/privacy" className="hover:text-muted">Privacy Policy</a>
            <a href="/terms" className="hover:text-muted">Terms of Service</a>
          </div>
        </div>
      </footer>
    </main>
  );
}

export default function Home() {
  return <Suspense><HomeContent /></Suspense>;
}
