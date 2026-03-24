import { NextRequest, NextResponse } from "next/server";
import { backendFetch } from "@/lib/fetch";

export async function GET(req: NextRequest) {
  const code = req.nextUrl.searchParams.get("code");
  const baseUrl = process.env.NEXT_PUBLIC_BASE_URL || "http://localhost:3000";

  if (!code) {
    return NextResponse.json(
      { error: "Missing authorization code" },
      { status: 400 }
    );
  }

  // Delegate token exchange entirely to the backend.
  // No retry on this call — auth codes are single-use, a retry with the
  // same code after a successful exchange would fail with invalid_grant.
  let backendRes: Response;
  try {
    backendRes = await backendFetch({
      path: "/auth/token",
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        code,
        redirect_uri: process.env.SOUNDCLOUD_REDIRECT_URI!,
      }),
      timeoutMs: 15_000,
      retries: 0, // Auth codes are single-use — no retries
    });
  } catch (err) {
    const isTimeout =
      err instanceof DOMException && err.name === "TimeoutError";
    console.error("Backend token exchange failed:", err);
    return NextResponse.redirect(
      `${baseUrl}/?error=${isTimeout ? "timeout" : "service_unavailable"}`
    );
  }

  if (!backendRes.ok) {
    const errorText = await backendRes.text();
    console.error(
      "Backend token exchange error:",
      backendRes.status,
      errorText
    );
    if (backendRes.status === 400) {
      return NextResponse.redirect(`${baseUrl}/?error=auth_failed`);
    }
    return NextResponse.redirect(`${baseUrl}/?error=exchange_failed`);
  }

  const data = await backendRes.json();
  const response = NextResponse.redirect(`${baseUrl}/dashboard`);

  response.cookies.set("cybaop_token", data.access_token, {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "lax",
    path: "/",
    maxAge: 60 * 60 * 24 * 30,
  });

  return response;
}
