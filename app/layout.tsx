import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "CybaOp — Intelligence Layer for SoundCloud Creators",
  description:
    "Analytics intelligence for SoundCloud creators. Engagement rates, trend detection, release timing, and AI-powered insights.",
  metadataBase: new URL("https://cyba-op.vercel.app"),
  alternates: { canonical: "/" },
  openGraph: {
    title: "CybaOp — Intelligence Layer for SoundCloud Creators",
    description:
      "Analytics intelligence for SoundCloud creators. Engagement rates, trend detection, release timing, and AI-powered insights.",
    url: "https://cyba-op.vercel.app",
    siteName: "CybaOp",
    type: "website",
    images: [
      {
        url: "/og-image.png",
        width: 1200,
        height: 630,
        alt: "CybaOp — Intelligence Layer for SoundCloud Creators",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "CybaOp — Intelligence Layer for SoundCloud Creators",
    description: "Analytics intelligence for SoundCloud creators.",
    images: ["/og-image.png"],
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased bg-background text-foreground min-h-screen`}
      >
        {children}
      </body>
    </html>
  );
}
