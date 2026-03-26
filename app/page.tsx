"use client";

import { useSearchParams } from "next/navigation";
import { Suspense } from "react";

const ERROR_MESSAGES: Record<string, string> = {
  auth_failed: "Authentication failed — please try again.",
  timeout: "The server took too long to respond. Try again in a moment.",
  service_unavailable: "Authentication service is temporarily unavailable.",
  exchange_failed: "Something went wrong during sign-in. Please try again.",
};

function HomeContent() {
  const params = useSearchParams();
  const error = params.get("error");

  return (
    <main className="min-h-screen flex flex-col items-center justify-center px-6">
      {/* Subtle gradient background */}
      <div className="fixed inset-0 bg-gradient-to-b from-background via-background to-[#0f0f0f] -z-10" />

      {/* Glow effect behind the card */}
      <div className="fixed top-1/3 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[400px] bg-accent/5 rounded-full blur-[120px] -z-10" />

      <div className="max-w-2xl text-center space-y-8">
        {/* Logo / Brand */}
        <div className="space-y-2">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-border text-xs text-muted tracking-wide uppercase">
            <span className="w-1.5 h-1.5 rounded-full bg-accent animate-pulse" />
            Beta
          </div>
          <h1 className="text-5xl sm:text-6xl font-bold tracking-tight">
            Cyba<span className="text-accent">Op</span>
          </h1>
        </div>

        {/* Tagline */}
        <p className="text-lg sm:text-xl text-muted max-w-lg mx-auto leading-relaxed">
          The intelligence layer for SoundCloud creators. Reconstruct your
          creative evolution. Surface your strongest era.
        </p>

        {/* Error banner */}
        {error && (
          <div className="mx-auto max-w-md px-4 py-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-sm">
            {ERROR_MESSAGES[error] || "An unexpected error occurred."}
          </div>
        )}

        {/* CTA */}
        <div className="flex flex-col items-center gap-4">
          <a
            href="/api/auth/soundcloud"
            className="inline-flex items-center gap-2 px-6 py-3 bg-accent hover:bg-accent-hover text-white font-medium rounded-lg transition-colors"
          >
            <SoundCloudIcon />
            Connect SoundCloud
          </a>
          <p className="text-xs text-muted">
            We only read your public profile and track data. Nothing is modified.
          </p>
        </div>

        {/* Feature hints */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-8 border-t border-border">
          <FeatureCard
            icon="📊"
            title="Track Analytics"
            description="Engagement rates, play patterns, and catalog performance"
          />
          <FeatureCard
            icon="📈"
            title="Trend Detection"
            description="Growth velocity, peak periods, and release timing"
          />
          <FeatureCard
            icon="🧠"
            title="AI Insights"
            description="Actionable recommendations powered by your data"
          />
        </div>
      </div>
    </main>
  );
}

function FeatureCard({
  icon,
  title,
  description,
}: {
  icon: string;
  title: string;
  description: string;
}) {
  return (
    <div className="p-4 rounded-lg border border-border bg-surface text-left space-y-2">
      <span className="text-2xl">{icon}</span>
      <h3 className="text-sm font-semibold">{title}</h3>
      <p className="text-xs text-muted leading-relaxed">{description}</p>
    </div>
  );
}

function SoundCloudIcon() {
  return (
    <svg
      width="20"
      height="20"
      viewBox="0 0 24 24"
      fill="currentColor"
      aria-hidden="true"
    >
      <path d="M1 18V11h1v7H1zm3 1V9h1v10H4zm3-1V7h1v11H7zm3 1V5h1v14h-1zm3-1V8h1v10h-1zm3 1V6h1v13h-1zm3-2V3h1v14h-1z" />
    </svg>
  );
}

export default function Home() {
  return (
    <Suspense>
      <HomeContent />
    </Suspense>
  );
}
