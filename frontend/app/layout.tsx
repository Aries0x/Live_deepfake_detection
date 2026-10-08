import type { Metadata } from "next";
import Navbar from "@/components/Navbar";
import "./globals.css";

export const metadata: Metadata = {
  title: "SecureCall — Real-Time Multimodal Media Integrity",
  description: "Live WebRTC call forensics: facial manipulation, voice clone anti-spoofing, temporal consistency, and tamper-evident audit trails.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark h-full bg-[#0b0f19]">
      <body className="min-h-full flex flex-col bg-[#0b0f19] text-slate-100 antialiased">
        <Navbar />
        <main className="flex-1">{children}</main>
      </body>
    </html>
  );
}
