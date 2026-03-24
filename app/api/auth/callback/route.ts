import { NextRequest, NextResponse } from "next/server";

const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8000";
const TOKEN_EXCHANGE_TIMEOUT_MS = 15_000; // 15s — matches backend's httpx timeout to SoundCloud

export async function GET(req: NextRequest) {
  const code = req.nextUrl.searchParams.get("code");

  if (!code) {
    return NextResponse.json(
      { error: "Missing authorization code" },
      { status: 400 }
    );
  }

  // Delegate token exchange entirely to the backend.
  // The backend is the single owner of: SoundCloud creds, token exchange,
  // profile fetch, user persistence, and JWT issuance.
  // If the backend is down, auth fails — no silent fallback to a different
  // token type, which would create divergent auth states downstream.
  let backendRes: Response;
  try {
    backendRes = await fetch(`${BACKEND_URL}/auth/token`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        code,
        redirect_uri: process.env.SOUNDCLOUD_REDIRECT_URI!,
      }),
      signal: AbortSignal.timeout(TOKEN_EXCHANGE_TIMEOUT_MS),
    });
  } catch (err) {
    const isTimeout = err instanceof DOMException && err.name === "TimeoutError";
    console.error(
      isTimeout ? "Backend token exchange timed out" : "Backend unreachable during token exchange:",
      err
    );
    return NextResponse.redirect(
      `${process.env.NEXT_PUBLIC_BASE_URL}/?error=${isTimeout ? "timeout" : "service_unavailable"}`
    );
  }

  if (!backendRes.ok) {
    const errorText = await backendRes.text();
    console.error("Backend token exchange failed:", backendRes.status, errorText);

    if (backendRes.status === 400) {
      // Invalid/expired code — user needs to re-authorize
      return NextResponse.redirect(
        `${process.env.NEXT_PUBLIC_BASE_URL}/?error=auth_failed`
      );
    }
    return NextResponse.redirect(
      `${process.env.NEXT_PUBLIC_BASE_URL}/?error=exchange_failed`
    );
  }

  const data = await backendRes.json();

  const response = NextResponse.redirect(
    `${process.env.NEXT_PUBLIC_BASE_URL}/dashboard`
  );

  // Single auth cookie — the CybaOp JWT from the backend.
  // This is the only token the frontend ever sees or stores.
  response.cookies.set("cybaop_token", data.access_token, {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "lax",
    path: "/",
    maxAge: 60 * 60 * 24 * 30, // 30 days, matches backend JWT expiry
  });

  return response;
}
