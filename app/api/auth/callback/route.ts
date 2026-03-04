import { NextRequest, NextResponse } from "next/server";

export async function GET(req: NextRequest) {
  const code = req.nextUrl.searchParams.get("code");

  if (!code) {
    return NextResponse.json(
      { error: "Missing authorization code" },
      { status: 400 }
    );
  }

  const tokenResponse = await fetch(
    "https://api.soundcloud.com/oauth2/token",
    {
      method: "POST",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
      },
      body: new URLSearchParams({
        client_id: process.env.SOUNDCLOUD_CLIENT_ID!,
        client_secret: process.env.SOUNDCLOUD_CLIENT_SECRET!,
        redirect_uri: process.env.SOUNDCLOUD_REDIRECT_URI!,
        grant_type: "authorization_code",
        code,
      }),
    }
  );

  if (!tokenResponse.ok) {
    const errorData = await tokenResponse.text();
    return NextResponse.json(
      { error: "Token exchange failed", details: errorData },
      { status: 500 }
    );
  }

  const tokenData = await tokenResponse.json();

  const response = NextResponse.redirect(
    `${process.env.NEXT_PUBLIC_BASE_URL}/dashboard`
  );

  // Store securely
  response.cookies.set("sc_access_token", tokenData.access_token, {
    httpOnly: true,
    secure: true,
    sameSite: "lax",
    path: "/",
  });

  return response;
}








