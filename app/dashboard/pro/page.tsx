"use client";

import { useEffect, useState, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { TopNav, BottomNav } from "../components/nav";

interface BillingStatus {
  tier: string;
  is_pro: boolean;
  features: Record<string, boolean>;
  subscription_status: string | null;
  subscription_ends_at: string | null;
  warning: string | null;
}

const PRO_FEATURES = [
  { icon: "🧠", name: "AI-Powered Insights", desc: "Gemini analyzes your catalog and gives personalized strategy recommendations. Not generic tips — real analysis of your numbers." },
  { icon: "📈", name: "Growth Velocity", desc: "Track your 7-day, 30-day, and 90-day growth rates. Know if you're accelerating or stalling before it's obvious." },
  { icon: "🔍", name: "Trend Detection", desc: "Automatic detection of anomaly tracks, peak periods, and momentum shifts across your catalog." },
  { icon: "📉", name: "Engagement Decay", desc: "See exactly how fast plays drop off after release. Time your promotions to maximize each track's lifecycle." },
  { icon: "🚨", name: "Anomaly Alerts", desc: "Get flagged when a track is significantly over or underperforming relative to your catalog average." },
  { icon: "♾️", name: "Unlimited History", desc: "Free tier keeps 30 days of snapshots. Pro keeps everything — the longer you use CybaOp, the smarter it gets." },
  { icon: "⚡", name: "Priority Refresh", desc: "Your analytics pipeline runs first. No waiting behind the queue during peak hours." },
];

function ProPageContent() {
  const [status, setStatus] = useState<BillingStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [upgrading, setUpgrading] = useState(false);
  const [managing, setManaging] = useState(false);
  const router = useRouter();
  const searchParams = useSearchParams();
  const sessionId = searchParams.get("session_id");

  useEffect(() => {
    fetch("/api/billing/status")
      .then((r) => { if (r.status === 401) { router.push("/?error=auth_failed"); return null; } return r.json(); })
      .then((d) => { if (d) setStatus(d); setLoading(false); })
      .catch(() => setLoading(false));
  }, [router]);

  async function handleUpgrade() {
    setUpgrading(true);
    try {
      const res = await fetch("/api/billing/checkout", { method: "POST" });
      const data = await res.json();
      if (data.url) {
        window.location.href = data.url;
        return;
      }
    } catch {}
    setUpgrading(false);
  }

  async function handleManage() {
    setManaging(true);
    try {
      const res = await fetch("/api/billing/portal", { method: "POST" });
      const data = await res.json();
      if (data.url) {
        window.location.href = data.url;
        return;
      }
    } catch {}
    setManaging(false);
  }

  const isPro = status?.is_pro || false;
  const subscriptionStatus = status?.subscription_status;

  return (
    <div className="min-h-screen pb-20 md:pb-0">
      <TopNav />
      <div className="md:hidden px-4 pt-4 pb-2 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <a href="/dashboard" className="text-lg font-bold">Cyba<span className="text-accent">Op</span></a>
          <span className="text-xs text-muted">/ pro</span>
        </div>
        <a href="/dashboard" className="text-xs text-muted">← Back</a>
      </div>

      <div className="max-w-3xl mx-auto px-4 sm:px-6 py-6 sm:py-10 space-y-8 animate-page-enter">
        {/* Hero */}
        <div className="text-center space-y-3">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-violet-dim border border-violet/20 text-xs text-violet uppercase tracking-wider">
            {isPro ? "✓ Active" : "Upgrade"}
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold">
            CybaOp <span className="text-violet">Pro</span>
          </h1>
          <p className="text-muted text-sm max-w-md mx-auto">
            {isPro
              ? "You have full access to AI insights, trend detection, and unlimited history."
              : "Stop guessing. Let AI analyze your catalog and tell you exactly what's working."}
          </p>
        </div>

        {/* Success banner after Stripe checkout return */}
        {sessionId && (
          <div className="rounded-xl border border-lime/30 bg-lime-dim p-4 text-center space-y-1 animate-fade-in">
            <p className="text-sm font-semibold text-lime">🎉 Payment successful!</p>
            <p className="text-xs text-muted">Your Pro access is being activated. It may take a moment to reflect.</p>
          </div>
        )}

        {/* Past due warning banner */}
        {isPro && subscriptionStatus === "past_due" && status?.warning && (
          <div className="rounded-xl border border-amber/30 bg-amber-dim p-4 text-center space-y-2 animate-fade-in">
            <p className="text-sm font-semibold text-amber">⚠️ {status.warning}</p>
            <button
              onClick={handleManage}
              disabled={managing}
              className="px-4 py-2 bg-amber hover:brightness-110 text-black font-semibold rounded-xl text-sm disabled:opacity-50"
            >
              {managing ? "Loading..." : "Update Payment"}
            </button>
          </div>
        )}

        {/* Pricing card — show when not pro */}
        {!isPro && !loading && (
          <div className="rounded-2xl border border-violet/30 bg-violet-dim p-6 sm:p-8 text-center space-y-4 card-lift">
            <div className="space-y-1">
              <p className="text-3xl font-black font-mono">$12<span className="text-base font-normal text-muted">/mo</span></p>
              <p className="text-xs text-muted">Cancel anytime. No contracts.</p>
            </div>
            <button
              onClick={handleUpgrade}
              disabled={upgrading}
              className="w-full py-3 bg-violet hover:brightness-110 text-white font-semibold rounded-xl text-sm disabled:opacity-50"
            >
              {upgrading ? "Redirecting to checkout..." : "Upgrade to Pro"}
            </button>
            <p className="text-[10px] text-muted">Beta pricing — locked in for early adopters</p>
          </div>
        )}

        {/* Active subscription card */}
        {isPro && subscriptionStatus === "active" && (
          <div className="rounded-2xl border border-lime/30 bg-lime-dim p-6 text-center space-y-3">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-lime/10 border border-lime/30 text-xs text-lime">
              ● Active subscription
            </div>
            <p className="text-xs text-muted">All features unlocked. Your next analytics run will include AI insights.</p>
            <div className="flex flex-col sm:flex-row items-center justify-center gap-3 mt-2">
              <a href="/dashboard/analytics" className="px-4 py-2 bg-accent hover:bg-accent-hover text-white rounded-xl text-sm">Run Analytics →</a>
              <button
                onClick={handleManage}
                disabled={managing}
                className="px-4 py-2 border border-border hover:bg-surface-hover text-foreground rounded-xl text-sm disabled:opacity-50"
              >
                {managing ? "Loading..." : "Manage Subscription"}
              </button>
            </div>
          </div>
        )}

        {/* Pro card for past_due or other pro states (not active) */}
        {isPro && subscriptionStatus !== "active" && subscriptionStatus !== "past_due" && (
          <div className="rounded-2xl border border-lime/30 bg-lime-dim p-6 text-center space-y-2">
            <p className="text-lg font-semibold text-lime">You&apos;re on Pro</p>
            <p className="text-xs text-muted">All features unlocked. Your next analytics run will include AI insights.</p>
            <a href="/dashboard/analytics" className="inline-block mt-2 px-4 py-2 bg-accent hover:bg-accent-hover text-white rounded-xl text-sm">Run Analytics →</a>
          </div>
        )}

        {/* Feature grid */}
        <div className="space-y-4">
          <h2 className="text-lg font-semibold text-center">What you get with Pro</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 stagger-children">
            {PRO_FEATURES.map((f) => (
              <div key={f.name} className="rounded-xl border border-border bg-surface p-4 space-y-2 card-lift">
                <div className="flex items-center gap-2">
                  <span className="text-lg">{f.icon}</span>
                  <h3 className="text-sm font-semibold">{f.name}</h3>
                  {isPro && <span className="text-[10px] text-lime">✓</span>}
                </div>
                <p className="text-xs text-muted leading-relaxed">{f.desc}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Comparison */}
        <div className="rounded-xl border border-border overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-surface border-b border-border">
                <th className="text-left px-4 py-3 text-xs text-muted uppercase">Feature</th>
                <th className="text-center px-4 py-3 text-xs text-muted uppercase">Free</th>
                <th className="text-center px-4 py-3 text-xs text-violet uppercase">Pro</th>
              </tr>
            </thead>
            <tbody className="text-xs">
              {[
                ["Engagement metrics", true, true],
                ["Catalog health", true, true],
                ["Release timing", true, true],
                ["Era timeline", true, true],
                ["Plays history", "30 days", "Unlimited"],
                ["AI insights", false, true],
                ["Growth velocity", false, true],
                ["Trend detection", false, true],
                ["Anomaly alerts", false, true],
                ["Engagement decay", false, true],
              ].map(([feature, free, pro]) => (
                <tr key={feature as string} className="border-b border-border last:border-0">
                  <td className="px-4 py-2.5 text-muted">{feature as string}</td>
                  <td className="px-4 py-2.5 text-center">{free === true ? <span className="text-lime">✓</span> : free === false ? <span className="text-muted">—</span> : <span className="text-muted">{free as string}</span>}</td>
                  <td className="px-4 py-2.5 text-center">{pro === true ? <span className="text-violet">✓</span> : <span className="text-violet">{pro as string}</span>}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
      <BottomNav />
    </div>
  );
}

export default function ProPage() {
  return (
    <Suspense fallback={<div className="min-h-screen flex items-center justify-center text-muted">Loading...</div>}>
      <ProPageContent />
    </Suspense>
  );
}
