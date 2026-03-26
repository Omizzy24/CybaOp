import { NextRequest, NextResponse } from "next/server";

const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8000";
const SC_EXCHANGE_TIMEOUT_MS = 10_000;
const BACKEND_TIMEOUT_MS = 8_000;
const COOKIE_MAX_AGE = 604800; // 7 days
const DEBUG = process.env.LOG_LEVEL === "debug";

function getBaseUrl(req: NextRequest): string | null {
  const host = req.headers.get("host") || process.env.VERCEL_URL;
  if (!host) return null;
  return `https://${host}`;
}

function makeSignal(ms: number): AbortSignal | undefined {
  if (typeof AbortSignal !== "undefined" && AbortSignal.timeout) {
    return AbortSignal.timeout(ms);
  }
  return undefined;
}

export async function GET(req: NextRequest) {
  // 1. Derive base URL — never use NEXT_PUBLIC_BASE_URL
  const baseUrl = getBaseUrl(req);
  if (!baseUrl) {
    return NextResponse.json({ error: "missing_host" }, { status: 500 });
  }

  try {
    const code = req.nextUrl.searchParams.get("code");
    if (!code) {
      return NextResponse.json(
        { error: "Missing authorization code" },
        { status: 400 }
      );
    }

    const redirectUri = process.env.SOUNDCLOUD_REDIRECT_URI!;

    if (DEBUG) {
      console.error(JSON.stringify({
        event: "callback_received",
        code_prefix: code.substring(0, 8),
        redirect_uri: redirectUri,
        host: req.headers.get("host"),
        base_url: baseUrl,
      }));
    }

    // 2. Exchange code with SoundCloud directly (fast, no Railway cold start)
    //    MUST use same redirect_uri as the authorization request
    //    NO retries — codes are single-use
    let scRes: Response;
    try {
      scRes = await fetch("https://api.soundcloud.com/oauth2/token", {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: new URLSearchParams({
          client_id: process.env.SOUNDCLOUD_CLIENT_ID!,
          client_secret: process.env.SOUNDCLOUD_CLIENT_SECRET!,
          redirect_uri: redirectUri,
          grant_type: "authorization_code",
          code,
        }),
        signal: makeSignal(SC_EXCHANGE_TIMEOUT_MS),
      });
    } catch (err) {
      console.error("SoundCloud exchange timeout/error:", err);
      return NextResponse.redirect(`${baseUrl}/?error=timeout`);
    }

    if (!scRes.ok) {
      const errBody = await scRes.text();
      console.error("SoundCloud exchange failed:", scRes.status, errBody);
      return NextResponse.redirect(`${baseUrl}/?error=auth_failed`);
    }

    const scTokenData = await scRes.json();
    const scAccessToken = scTokenData.access_token;

    if (!scAccessToken) {
      console.error("SoundCloud returned no access_token:", scTokenData);
      return NextResponse.redirect(`${baseUrl}/?error=auth_failed`);
    }

    // 3. Send SC token to backend for registration + JWT issuance
    //    NO retries — if backend is down, fail cleanly
    //    DO NOT store raw SC token as fallback
    let backendRes: Response;
    try {
      backendRes = await fetch(`${BACKEND_URL}/auth/token-from-sc`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ access_token: scAccessToken }),
        signal: makeSignal(BACKEND_TIMEOUT_MS),
      });
    } catch (err) {
      console.error("Backend registration timeout/error:", err);
      return NextResponse.redirect(`${baseUrl}/?error=service_unavailable`);
    }

    if (!backendRes.ok) {
      const errBody = await backendRes.text();
      console.error("Backend registration failed:", backendRes.status, errBody);
      return NextResponse.redirect(`${baseUrl}/?error=service_unavailable`);
    }

    const jwtData = await backendRes.json();
    const cybaopJwt = jwtData.access_token;

    if (!cybaopJwt) {
      console.error("Backend returned no access_token:", jwtData);
      return NextResponse.redirect(`${baseUrl}/?error=service_unavailable`);
    }

    // 4. Set cookie and redirect to dashboard
    const response = NextResponse.redirect(`${baseUrl}/dashboard`);
    response.cookies.set("cybaop_token", cybaopJwt, {
      httpOnly: true,
      secure: true,
      sameSite: "lax",
      path: "/",
      maxAge: COOKIE_MAX_AGE,
    });

    if (DEBUG) {
      console.error(JSON.stringify({
        event: "callback_success",
        redirect_to: `${baseUrl}/dashboard`,
        user_id: jwtData.user_id,
        username: jwtData.username,
      }));
    }

    return response;
  } catch (err) {
    console.error("Unhandled callback error:", err);
    return NextResponse.redirect(`${baseUrl!}/?error=unexpected`);
  }
}
