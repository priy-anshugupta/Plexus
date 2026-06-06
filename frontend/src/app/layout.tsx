import type { Metadata } from "next";
import { Inter, Outfit } from "next/font/google";
import "./globals.css";

const inter = Inter({
  variable: "--font-sans",
  subsets: ["latin"],
});

const outfit = Outfit({
  variable: "--font-display",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Plexus | Enterprise DevEx & Security Posture Platform",
  description: "Relational code intelligence, multi-agent automated audits, and autonomous remediation.",
};

import { RoleProvider } from "../context/RoleContext";

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${inter.variable} ${outfit.variable} h-full antialiased dark`}
    >
      <body className="min-h-full flex flex-col bg-background-dark text-slate-100 selection:bg-primary/20 selection:text-primary">
        <RoleProvider>
          {children}
        </RoleProvider>
      </body>
    </html>
  );
}

