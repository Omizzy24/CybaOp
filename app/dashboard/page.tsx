"use client";

import { useEffect, useState } from "react";

export default function Dashboard() {
  const [user, setUser] = useState<any>(null);

  useEffect(() => {
    fetch("/api/me")
      .then((res) => res.json())
      .then((data) => setUser(data));
  }, []);

  if (!user) return <div style={{ padding: 40 }}>Loading...</div>;

  return (
    <div style={{ padding: 40 }}>
      <h1>Welcome, {user.username}</h1>
      <p>Followers: {user.followers_count}</p>
      <p>Tracks: {user.track_count}</p>
    </div>
  );
}
