import { NextResponse } from "next/server";

export async function GET() {
  const clientId = process.env.SOUNDCLOUD_CLIENT_ID;
  const redirectUri = process.env.SOUNDCLOUD_REDIRECT_URI;

  if (!clientId || !redirectUri) {
    return NextResponse.json(
      { error: "OAuth environment variables missing" },
      { status: 500 }
    );
  }

  const url = new URL("https://soundcloud.com/connect");
  url.searchParams.set("client_id", clientId);
  url.searchParams.set("redirect_uri", redirectUri);
  url.searchParams.set("response_type", "code");
  url.searchParams.set("scope", "non-expiring");

  return NextResponse.redirect(url.toString());
}
