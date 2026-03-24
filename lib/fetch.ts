/**
 * Fetch wrapper with retry + timeout for backend calls.
 * Used by all Next.js API routes that proxy to FastAPI.
 */

const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8000";

interface BackendFetchOptions {
  path: string;
  method?: "GET" | "POST";
  headers?: Record<string, string>;
  body?: string;
  timeoutMs?: number;
  retries?: number;
}

export async function backendFetch({
  path,
  method = "GET",
  headers = {},
  body,
  timeoutMs = 10_000,
  retries = 2,
}: BackendFetchOptions): Promise<Response> {
  let lastError: unknown;

  for (let attempt = 0; attempt <= retries; attempt++) {
    try {
      const res = await fetch(`${BACKEND_URL}${path}`, {
        method,
        headers,
        body,
        signal: AbortSignal.timeout(timeoutMs),
      });
      // Don't retry on client errors (4xx) — those won't change
      if (res.ok || (res.status >= 400 && res.status < 500)) {
        return res;
      }
      // Server errors (5xx) are retryable
      lastError = new Error(`Backend ${res.status}`);
    } catch (err) {
      lastError = err;
    }

    // Exponential backoff: 200ms, 400ms
    if (attempt < retries) {
      await new Promise((r) => setTimeout(r, 200 * (attempt + 1)));
    }
  }

  throw lastError;
}
