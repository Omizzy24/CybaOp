import { NextResponse } from "next/server";

export async function GET() {
  const clientId = process.env.SOUNDCLOUD_CLIENT_ID;
  const redirectUri = process.env.SOUNDCLOUD_REDIRECT_URI;

  if (!clientId || !redirectUri) {
    return NextResponse.json(
      { error: "Missing SoundCloud environment variables" },
      { status: 500 }
    );
  }

  const soundcloudAuthUrl =
    `https://soundcloud.com/connect` +
    `?client_id=${clientId}` +
    `&redirect_uri=${encodeURIComponent(redirectUri)}` +
    `&response_type=code` +
    `&scope=non-expiring`;

  return NextResponse.redirect(soundcloudAuthUrl);
}

