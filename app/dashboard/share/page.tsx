"use client";
import { useEffect, useState, useRef, useCallback } from "react";
import { useRouter } from "next/navigation";
import { BottomNav } from "../components/nav";

interface ShareData { username: string; display_name: string; avatar_url: string; total_plays: number; top_track: string; engagement_rate: number; best_day: string | null; }

export default function SharePage() {
  const [data, setData] = useState<ShareData | null>(null);
  const [loading, setLoading] = useState(true);
  const [size, setSize] = useState<"story" | "twitter">("story");
  const cardRef = useRef<HTMLDivElement>(null);
  const router = useRouter();

  useEffect(() => {
    Promise.all([fetch("/api/auth/me").then(r => r.json()), fetch("/api/analytics").then(r => r.json())])
      .then(([profile, analytics]) => {
        if (profile.error || !analytics.success) { router.push("/?error=auth_failed"); return; }
        const rpt = analytics.report;
        setData({ username: profile.username, display_name: profile.display_name || profile.username, avatar_url: profile.avatar_url || "", total_plays: rpt?.metrics?.total_plays || 0, top_track: rpt?.top_tracks?.[0]?.title || "—", engagement_rate: rpt?.metrics?.avg_engagement_rate || 0, best_day: rpt?.trends?.best_release_day || null });
        setLoading(false);
      }).catch(() => setLoading(false));
  }, [router]);

  const handleDownload = useCallback(async () => {
    if (!cardRef.current) return;
    const { toPng } = await import("html-to-image");
    const url = await toPng(cardRef.current, { pixelRatio: 2 });
    const a = document.createElement("a"); a.download = `cybaop-${data?.username || "stats"}.png`; a.href = url; a.click();
  }, [data]);

  const dims = size === "story" ? { w: 360, h: 640 } : { w: 500, h: 280 };

  return (
    <div className="min-h-screen pb-20 md:pb-0">
      <div className="md:hidden px-4 pt-4 pb-2 flex items-center justify-between">
        <a href="/dashboard" className="text-lg font-bold">Cyba<span className="text-accent">Op</span></a>
        <a href="/dashboard" className="text-xs text-muted">← Back</a>
      </div>
      <div className="max-w-2xl mx-auto px-4 sm:px-6 py-6 sm:py-10 space-y-6">
        <div><h1 className="text-xl sm:text-2xl font-bold">Share Your Stats</h1><p className="text-muted text-sm mt-1">Download and share on social media</p></div>
        <div className="flex gap-2">
          <button onClick={() => setSize("story")} className={`px-3 py-1.5 rounded-lg text-xs ${size === "story" ? "bg-accent text-white" : "bg-surface border border-border text-muted"}`}>Stories</button>
          <button onClick={() => setSize("twitter")} className={`px-3 py-1.5 rounded-lg text-xs ${size === "twitter" ? "bg-accent text-white" : "bg-surface border border-border text-muted"}`}>Twitter</button>
        </div>
        {loading ? <div className="flex items-center justify-center h-64 text-muted text-sm">Loading...</div> : data ? (
          <>
            <div className="flex justify-center overflow-hidden">
              <div ref={cardRef} style={{ width: dims.w, height: dims.h }} className="rounded-2xl bg-gradient-to-b from-[#050505] to-[#0a0a0a] border border-white/10 p-6 flex flex-col justify-between relative overflow-hidden">
                <div className="absolute top-0 right-0 w-32 h-32 bg-accent/5 rounded-full blur-[60px]" />
                <div><p className="text-xs text-accent font-semibold tracking-wider uppercase">CybaOp</p>
                  <div className="flex items-center gap-3 mt-3">{data.avatar_url && <img src={data.avatar_url} alt="" className="w-10 h-10 rounded-full" />}<div><p className="font-bold text-white">{data.display_name}</p><p className="text-xs text-muted">@{data.username}</p></div></div></div>
                <div className="space-y-4">
                  <div><p className="text-xs text-muted uppercase tracking-wide">Total Plays</p><p className="text-4xl font-black text-white font-mono tabular-nums">{data.total_plays.toLocaleString()}</p></div>
                  <div className="grid grid-cols-2 gap-3"><div><p className="text-[10px] text-muted uppercase">Top Track</p><p className="text-sm font-semibold text-white truncate">{data.top_track}</p></div><div><p className="text-[10px] text-muted uppercase">Engagement</p><p className="text-sm font-semibold text-accent">{(data.engagement_rate * 100).toFixed(1)}%</p></div></div>
                  {data.best_day && <div><p className="text-[10px] text-muted uppercase">Best Release Day</p><p className="text-sm font-semibold text-white">{data.best_day}</p></div>}
                </div>
                <p className="text-[9px] text-muted/40 text-center">cyba-op.vercel.app</p>
              </div>
            </div>
            <button onClick={handleDownload} className="w-full py-3 bg-accent hover:bg-accent-hover text-white font-semibold rounded-xl">Download PNG</button>
          </>
        ) : <p className="text-muted text-center">No data available</p>}
      </div>
      <BottomNav />
    </div>
  );
}
