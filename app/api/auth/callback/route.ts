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
        retries: 0,
      });
    } catch (err) {
      console.error("Backend token exchange failed:", err);
      return NextResponse.redirect(
        `${baseUrl}/?error=service_unavailable`
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
      secure: true,
      sameSite: "lax",
      path: "/",
      maxAge: 60 * 60 * 24 * 30,
    });

    return response;
  } catch (err) {
    // Catch-all: never return a raw 500 to the user
    console.error("Unhandled callback error:", err);
    return NextResponse.redirect(`${baseUrl}/?error=unexpected`);
  }
}
