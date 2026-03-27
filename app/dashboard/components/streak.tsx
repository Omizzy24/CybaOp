"use client";

import { useEffect, useState } from "react";

/**
 * Streak tracker — counts consecutive days the user has checked analytics.
 * Stored in localStorage (client-only, no backend needed).
 */

const STORAGE_KEY = "cybaop_streak";

interface StreakData {
  current: number;
  lastDate: string; // ISO date string YYYY-MM-DD
  best: number;
}

function getToday(): string {
  return new Date().toISOString().slice(0, 10);
}

function getYesterday(): string {
  const d = new Date();
  d.setDate(d.getDate() - 1);
  return d.toISOString().slice(0, 10);
}

function loadStreak(): StreakData {
  if (typeof window === "undefined") return { current: 0, lastDate: "", best: 0 };
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) return JSON.parse(raw);
  } catch {}
  return { current: 0, lastDate: "", best: 0 };
}

function recordVisit(): StreakData {
  const streak = loadStreak();
  const today = getToday();

  if (streak.lastDate === today) return streak; // already counted today

  if (streak.lastDate === getYesterday()) {
    streak.current += 1;
  } else {
    streak.current = 1;
  }

  streak.lastDate = today;
  streak.best = Math.max(streak.best, streak.current);

  try { localStorage.setItem(STORAGE_KEY, JSON.stringify(streak)); } catch {}
  return streak;
}

export function StreakBadge() {
  const [streak, setStreak] = useState<StreakData>({ current: 0, lastDate: "", best: 0 });

  useEffect(() => {
    setStreak(recordVisit());
  }, []);

  if (streak.current === 0) return null;

  const flames = Math.min(streak.current, 7);

  return (
    <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-amber-dim border border-amber/20">
      <span className="animate-flame text-base" role="img" aria-label="streak">🔥</span>
      <span className="text-xs font-semibold text-amber">{streak.current} day streak</span>
      {/* Mini flame trail */}
      <div className="flex gap-0.5" aria-hidden="true">
        {Array.from({ length: 7 }).map((_, i) => (
          <span
            key={i}
            className="w-1.5 h-1.5 rounded-full"
            style={{
              background: i < flames ? "var(--amber)" : "var(--border)",
              opacity: i < flames ? 1 - i * 0.1 : 0.3,
            }}
          />
        ))}
      </div>
    </div>
  );
}
