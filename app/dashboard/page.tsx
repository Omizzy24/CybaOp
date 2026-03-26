"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

interface UserData {
  username?: string;
  display_name?: string;
  user_id?: string;
  tier?: string;
  followers_count?: number;
  following_count?: number;
  track_count?: number;
  playlist_count?: number;
  likes_count?: number;
  avatar_url?: string;
  profile_url?: string;
}

export default function Dashboard() {
  const [user, setUser] = useState<UserData | null>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    fetch("/api/auth/me")
      .then((res) => {
        if (res.status === 401) {
          router.push("/?error=auth_failed");
          return null;
        }
        return res.json();
      })
      .then((data) => {
        if (data && !data.error) setUser(data);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, [router]);

  async function handleLogout() {
    await fetch("/api/auth/logout", { method: "POST" });
    router.push("/");
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="flex items-center gap-3 text-muted">
          <div className="w-5 h-5 border-2 border-muted border-t-accent rounded-full animate-spin" />
          Loading your profile...
        </div>
      </div>
    );
  }

  if (!user) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center gap-4">
        <p className="text-muted">Not authenticated</p>
        <a
          href="/api/auth/soundcloud"
          className="px-4 py-2 bg-accent hover:bg-accent-hover text-white rounded-lg text-sm transition-colors"
        >
          Connect SoundCloud
        </a>
      </div>
    );
  }

  return (
    <div className="min-h-screen">
      {/* Nav */}
      <nav className="border-b border-border px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <span className="text-lg font-bold">
            Cyba<span className="text-accent">Op</span>
          </span>
          <span className="text-xs text-muted px-2 py-0.5 rounded-full border border-border uppercase tracking-wide">
            {user.tier || "free"}
          </span>
        </div>
        <div className="flex items-center gap-4">
          {user.avatar_url && (
            <img
              src={user.avatar_url}
              alt=""
              className="w-8 h-8 rounded-full"
            />
          )}
          <span className="text-sm text-muted">{user.username}</span>
          <button
            onClick={handleLogout}
            className="text-sm text-muted hover:text-foreground px-3 py-1.5 rounded-md border border-border hover:border-muted transition-colors"
          >
            Sign out
          </button>
        </div>
      </nav>

      {/* Main content */}
      <div className="max-w-5xl mx-auto px-6 py-10 space-y-8">
        {/* Welcome header */}
        <div>
          <h1 className="text-2xl font-bold">
            Welcome back, {user.display_name || user.username}
          </h1>
          <p className="text-muted text-sm mt-1">
            Here&apos;s your SoundCloud overview
          </p>
        </div>

        {/* Stats grid */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <StatCard label="Tracks" value={user.track_count} />
          <StatCard label="Followers" value={user.followers_count} />
          <StatCard label="Following" value={user.following_count} />
          <StatCard label="Likes" value={user.likes_count} />
        </div>

        {/* Analytics link */}
        <a
          href="/dashboard/analytics"
          className="block rounded-lg border border-border bg-surface hover:bg-surface-hover p-6 text-center space-y-2 transition-colors"
        >
          <p className="text-sm font-medium">📊 View Analytics</p>
          <p className="text-xs text-muted">
            Track engagement, trend detection, and AI-powered insights
          </p>
        </a>
      </div>
    </div>
  );
}

function StatCard({
  label,
  value,
}: {
  label: string;
  value?: number;
}) {
  return (
    <div className="rounded-lg border border-border bg-surface p-4 space-y-1">
      <p className="text-xs text-muted uppercase tracking-wide">{label}</p>
      <p className="text-2xl font-bold font-mono">
        {value !== undefined ? value.toLocaleString() : "—"}
      </p>
    </div>
  );
}
