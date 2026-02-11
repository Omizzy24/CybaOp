export default function Home() {
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

        <a href="/api/auth/soundcloud" style={styles.button}>
          Connect SoundCloud
        </a>
      </div>
    </main>
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
  },
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
