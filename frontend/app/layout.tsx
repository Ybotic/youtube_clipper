import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AI Clipper",
  description: "Turn long videos into ready-to-post Shorts and Reels.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
