import type { Metadata } from "next";
import localFont from "next/font/local";
import "./globals.css";

import { Toaster } from "@/components/ui/sonner";
import { AuthProvider } from "@/lib/auth";

const geistSans = localFont({
  src: "./fonts/GeistVF.woff",
  variable: "--font-geist-sans",
});
const geistMono = localFont({
  src: "./fonts/GeistMonoVF.woff",
  variable: "--font-geist-mono",
});

export const metadata: Metadata = {
  title: "Parallel",
  description:
    "Your parallel self — a calm companion that remembers, plans, and gently nudges.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      {/* suppressHydrationWarning: browser extensions (e.g. ColorZilla injects
          `cz-shortcut-listen`) mutate <body> attributes before React hydrates,
          producing a spurious mismatch. This is scoped to <body> only, so a real
          mismatch anywhere in the app tree still surfaces. */}
      <body
        suppressHydrationWarning
        className={`${geistSans.variable} ${geistMono.variable} font-sans antialiased`}
      >
        <AuthProvider>{children}</AuthProvider>
        <Toaster position="top-center" />
      </body>
    </html>
  );
}
