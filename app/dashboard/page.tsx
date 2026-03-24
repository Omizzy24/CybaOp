"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

interface UserData {
  username?: string;
  display_name?: string;
  user_id?: string;
  tier?: string;
  followers_count?: number;
  track_count?: number;
  avatar_url?: string;
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
    return <div style={styles.container}>Loading...</div>;
  }

  if (!user) {
    return (
      <div style={styles.container}>
        <h1>Not authenticated</h1>
        <a href="/api/auth/soundcloud" style={styles.link}>Connect SoundCloud</a>
      </div>
    );
  }

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <h1>Welcome, {user.display_name || user.username}</h1>
        <button onClick={handleLogout} style={styles.logoutBtn}>
          Sign out
        </button>
      </div>

      <div style={styles.stats}>
        {user.tier && <span style={styles.badge}>{user.tier}</span>}
        {user.followers_count !== undefined && <p>Followers: {user.followers_count}</p>}
        {user.track_count !== undefined && <p>Tracks: {user.track_count}</p>}
      </div>
    </div>
  );
}

const styles = {
  container: {
    padding: "2rem",
    fontFamily: "system-ui, sans-serif",
    maxWidth: "800px",
    margin: "0 auto",
  },
  header: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: "2rem",
  },
  logoutBtn: {
    padding: "0.5rem 1rem",
    backgroundColor: "transparent",
    border: "1px solid #666",
    color: "#666",
    borderRadius: "6px",
    cursor: "pointer",
    fontSize: "0.9rem",
  },
  stats: {
    display: "flex",
    flexDirection: "column" as const,
    gap: "0.5rem",
  },
  badge: {
    display: "inline-block",
    padding: "0.25rem 0.75rem",
    backgroundColor: "#1e293b",
    borderRadius: "12px",
    fontSize: "0.8rem",
    textTransform: "uppercase" as const,
    letterSpacing: "0.05em",
    width: "fit-content",
  },
  link: {
    color: "#f97316",
  },
};
