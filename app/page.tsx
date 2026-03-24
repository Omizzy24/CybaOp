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
    <main style={styles.container}>
      <div style={styles.card}>
        <h1 style={styles.title}>
          CybaOp — The Intelligence Layer for SoundCloud Creators
        </h1>

        <p style={styles.subtitle}>
          Reconstruct your creative evolution. Surface your strongest era.
          Release with clarity.
        </p>

        {error && (
          <p style={styles.error}>
            {ERROR_MESSAGES[error] || "An unexpected error occurred."}
          </p>
        )}

        <a href="/api/auth/soundcloud" style={styles.button}>
          Connect SoundCloud
        </a>
      </div>
    </main>
  );
}

export default function Home() {
  return (
    <Suspense>
      <HomeContent />
    </Suspense>
  );
}

const styles = {
  container: {
    height: "100vh",
    display: "flex",
    justifyContent: "center",
    alignItems: "center",
    backgroundColor: "#0f172a",
    color: "#ffffff",
    fontFamily: "system-ui, sans-serif",
  } as const,
  card: {
    maxWidth: "700px",
    textAlign: "center" as const,
    padding: "2rem",
  },
  title: {
    fontSize: "2.5rem",
    fontWeight: 600,
    marginBottom: "1rem",
  },
  subtitle: {
    fontSize: "1.2rem",
    opacity: 0.8,
    marginBottom: "2rem",
  },
  error: {
    backgroundColor: "rgba(239, 68, 68, 0.15)",
    border: "1px solid rgba(239, 68, 68, 0.3)",
    color: "#fca5a5",
    padding: "0.75rem 1rem",
    borderRadius: "6px",
    marginBottom: "1.5rem",
    fontSize: "0.95rem",
  },
  button: {
    display: "inline-block",
    padding: "0.75rem 1.5rem",
    backgroundColor: "#f97316",
    color: "#fff",
    textDecoration: "none",
    borderRadius: "6px",
    fontWeight: 500,
  },
};
