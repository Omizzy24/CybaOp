"use client";

import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell,
  PieChart, Pie,
} from "recharts";

interface TrackMetric {
  track_id: string;
  title: string;
  engagement_rate: number;
  performance_score: number;
  is_outlier: boolean;
  outlier_direction: string;
}

const ACCENT = "#f97316";
const MUTED = "#737373";
const BORDER = "#262626";
const SURFACE = "#141414";
const GREEN = "#22c55e";
const RED = "#ef4444";

const GENRE_COLORS = ["#f97316", "#3b82f6", "#a855f7", "#22c55e", "#eab308", "#ec4899"];

// --- Engagement Bar Chart ---

export function EngagementBarChart({ tracks }: { tracks: TrackMetric[] }) {
  const data = tracks.slice(0, 15).map((t) => ({
    name: t.title.length > 20 ? t.title.slice(0, 20) + "…" : t.title,
    rate: +(t.engagement_rate * 100).toFixed(2),
    isOutlier: t.is_outlier,
    direction: t.outlier_direction,
  }));

  return (
    <div className="rounded-lg border border-border bg-surface p-4 sm:p-5 space-y-3">
      <h3 className="text-sm font-semibold">Engagement by Track</h3>
      <div className="w-full" style={{ height: Math.max(200, data.length * 32) }}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} layout="vertical" margin={{ left: 0, right: 16, top: 0, bottom: 0 }}>
            <XAxis type="number" tick={{ fill: MUTED, fontSize: 10 }} axisLine={false} tickLine={false} />
            <YAxis type="category" dataKey="name" tick={{ fill: MUTED, fontSize: 10 }} width={120} axisLine={false} tickLine={false} />
            <Tooltip
              contentStyle={{ background: SURFACE, border: `1px solid ${BORDER}`, borderRadius: 8, fontSize: 12 }}
              labelStyle={{ color: "#ededed" }}
              formatter={(v: number) => [`${v}%`, "Engagement"]}
            />
            <Bar dataKey="rate" radius={[0, 4, 4, 0]}>
              {data.map((entry, i) => (
                <Cell
                  key={i}
                  fill={entry.isOutlier ? (entry.direction === "over" ? GREEN : RED) : ACCENT}
                />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

// --- Genre Donut Chart ---

interface GenreData {
  name: string;
  count: number;
}

export function GenreDonutChart({ genres, totalTracks }: { genres: GenreData[]; totalTracks: number }) {
  if (genres.length === 0) return null;

  return (
    <div className="rounded-lg border border-border bg-surface p-4 sm:p-5 space-y-3">
      <h3 className="text-sm font-semibold">Genre Distribution</h3>
      <div className="w-full h-[220px] relative">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={genres}
              dataKey="count"
              nameKey="name"
              cx="50%"
              cy="50%"
              innerRadius={60}
              outerRadius={90}
              paddingAngle={2}
              stroke="none"
            >
              {genres.map((_, i) => (
                <Cell key={i} fill={GENRE_COLORS[i % GENRE_COLORS.length]} />
              ))}
            </Pie>
            <Tooltip
              contentStyle={{ background: SURFACE, border: `1px solid ${BORDER}`, borderRadius: 8, fontSize: 12 }}
              formatter={(v: number, name: string) => [`${v} tracks`, name]}
            />
          </PieChart>
        </ResponsiveContainer>
        {/* Center text */}
        <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
          <span className="text-2xl font-bold font-mono tabular-nums">{totalTracks}</span>
          <span className="text-[10px] text-muted uppercase tracking-wide">tracks</span>
        </div>
      </div>
      {/* Legend */}
      <div className="flex flex-wrap gap-3 justify-center">
        {genres.map((g, i) => (
          <div key={g.name} className="flex items-center gap-1.5 text-xs text-muted">
            <span className="w-2 h-2 rounded-full" style={{ background: GENRE_COLORS[i % GENRE_COLORS.length] }} />
            {g.name || "Unknown"}
          </div>
        ))}
      </div>
    </div>
  );
}

// --- Release Day Heatmap ---

const DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

interface DayData {
  day: string;
  engagement: number;
  count: number;
}

export function ReleaseDayHeatmap({ dayData, bestDay }: { dayData: DayData[]; bestDay: string | null }) {
  if (dayData.length === 0) return null;

  const maxEngagement = Math.max(...dayData.map((d) => d.engagement), 0.001);

  return (
    <div className="rounded-lg border border-border bg-surface p-4 sm:p-5 space-y-3">
      <h3 className="text-sm font-semibold">Release Day Performance</h3>
      <div className="grid grid-cols-7 gap-2">
        {DAYS.map((day) => {
          const d = dayData.find((dd) => dd.day.startsWith(day));
          const intensity = d ? d.engagement / maxEngagement : 0;
          const isBest = bestDay?.startsWith(day);
          return (
            <div key={day} className="flex flex-col items-center gap-1">
              <span className="text-[10px] text-muted">{day}</span>
              <div
                className={`w-full aspect-square rounded-md flex items-center justify-center text-[10px] font-mono ${
                  isBest ? "ring-2 ring-accent" : ""
                }`}
                style={{
                  background: `rgba(249, 115, 22, ${Math.max(0.05, intensity * 0.6)})`,
                }}
              >
                {d ? d.count : 0}
              </div>
            </div>
          );
        })}
      </div>
      <p className="text-[10px] text-muted text-center">
        Number = tracks released · Color intensity = avg engagement
      </p>
    </div>
  );
}
