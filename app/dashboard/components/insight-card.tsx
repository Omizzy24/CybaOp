"use client";

interface InsightCardProps {
  icon: string;
  title: string;
  borderColor: string;
  bgColor: string;
  children: React.ReactNode;
}

export function InsightCard({ icon, title, borderColor, bgColor, children }: InsightCardProps) {
  return (
    <div className={`rounded-xl border ${borderColor} ${bgColor} p-4 sm:p-5 space-y-2 card-lift`}>
      <div className="flex items-center gap-2">
        <span className="text-lg">{icon}</span>
        <h3 className="text-sm font-semibold">{title}</h3>
      </div>
      {children}
    </div>
  );
}
