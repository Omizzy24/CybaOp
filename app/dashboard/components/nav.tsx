"use client";

import { usePathname } from "next/navigation";

interface NavProps {
  user?: {
    username?: string;
    avatar_url?: string;
    tier?: string;
  };
  onLogout?: () => void;
}

const tabs = [
  { href: "/dashboard", label: "Dashboard", icon: "📊" },
  { href: "/dashboard/triage", label: "Triage", icon: "🚨" },
  { href: "/dashboard/analytics", label: "Analytics", icon: "📈" },
  { href: "/dashboard/workflows", label: "Workflows", icon: "⚙️" },
  { href: "/dashboard/pro", label: "Pro", icon: "⚡" },
];

export function TopNav({ user, onLogout }: NavProps) {
  return (
    <nav className="hidden md:flex border-b border-border px-6 py-4 items-center justify-between">
      <div className="flex items-center gap-3">
        <a href="/dashboard" className="text-lg font-bold hover:opacity-80">
          Cyba<span className="text-accent">Op</span>
        </a>
        {user?.tier && (
          <span className="text-xs text-muted px-2 py-0.5 rounded-full border border-border uppercase tracking-wide">
            {user.tier}
          </span>
        )}
      </div>
      <div className="flex items-center gap-4">
        {user?.avatar_url && (
          <img src={user.avatar_url} alt="" className="w-8 h-8 rounded-full" />
        )}
        <span className="text-sm text-muted">{user?.username}</span>
        {onLogout && (
          <button
            onClick={onLogout}
            className="text-sm text-muted hover:text-foreground px-3 py-1.5 rounded-md border border-border hover:border-muted"
          >
            Sign out
          </button>
        )}
      </div>
    </nav>
  );
}

export function BottomNav() {
  const pathname = usePathname();

  return (
    <nav className="md:hidden fixed bottom-0 left-0 right-0 z-50 border-t border-border bg-background/80 backdrop-blur-xl">
      <div className="flex items-center justify-around h-16 pb-[env(safe-area-inset-bottom)]">
        {tabs.map((tab) => {
          const active = pathname === tab.href;
          return (
            <a
              key={tab.href}
              href={tab.href}
              className={`flex flex-col items-center gap-1 px-4 py-2 min-w-[64px] ${
                active ? "text-accent" : "text-muted"
              }`}
            >
              <span className="text-xl">{tab.icon}</span>
              <span className={`text-[10px] tracking-wide ${active ? "font-semibold" : ""}`}>
                {tab.label}
              </span>
              {active && (
                <span className="absolute bottom-[calc(env(safe-area-inset-bottom)+2px)] w-8 h-0.5 bg-accent rounded-full" />
              )}
            </a>
          );
        })}
      </div>
    </nav>
  );
}
