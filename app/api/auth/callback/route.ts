import { NextRequest, NextResponse } from "next/server";
import { backendFetch } from "@/lib/fetch";

export async function GET(req: NextRequest) {
  const baseUrl = process.env.NEXT_PUBLIC_BASE_URL || "http://localhost:3000";

  try {
    const code = req.nextUrl.searchParams.get("code");

    if (!code) {
      return NextResponse.json(
        { error: "Missing authorization code" },
        { status: 400 }
      );
    }

    // Step 1: Exchange code with SoundCloud directly from Vercel edge.
    // This must happen immediately — SoundCloud codes expire in ~30s.
    // Vercel → SoundCloud is fast. Railway cold starts would kill the code.
    const scRes = await fetch("https://api.soundcloud.com/oauth2/token", {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: new URLSearchParams({
        client_id: process.env.SOUNDCLOUD_CLIENT_ID!,
        client_secret: process.env.SOUNDCLOUD_CLIENT_SECRET!,
        redirect_uri: process.env.SOUNDCLOUD_REDIRECT_URI!,
        grant_type: "authorization_code",
        code,
      }),
    });

    if (!scRes.ok) {
      const err = await scRes.text();
      console.error("SoundCloud token exchange failed:", scRes.status, err);
      return NextResponse.redirect(`${baseUrl}/?error=auth_failed`);
    }

    const scToken = await scRes.json();
    const accessToken = scToken.access_token;

    // Step 2: Send the SC token to the backend for profile fetch + persistence.
    // This is fire-and-forget style — we don't block the user on it.
    // If the backend is slow/down, the user still gets logged in.
    let cybaopToken = accessToken; // fallback: use SC token directly
    try {
      const backendRes = await backendFetch({
        path: "/auth/token-from-sc",
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ access_token: accessToken }),
        timeoutMs: 10_000,
        retries: 1,
      });

      if (backendRes.ok) {
        const data = await backendRes.json();
        cybaopToken = data.access_token;
      }
    } catch (err) {
      // Backend unavailable — fall back to SC token for now
      console.error("Backend registration failed, using SC token:", err);
    }

    const response = NextResponse.redirect(`${baseUrl}/dashboard`);
    response.cookies.set("cybaop_token", cybaopToken, {
      httpOnly: true,
      secure: true,
      sameSite: "lax",
      path: "/",
      maxAge: 60 * 60 * 24 * 30,
    });

    return response;
  } catch (err) {
    console.error("Unhandled callback error:", err);
    return NextResponse.redirect(`${baseUrl}/?error=unexpected`);
  }
}
