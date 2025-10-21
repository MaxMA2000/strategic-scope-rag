import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { IconSidebar } from "@/components/IconSidebar";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Strategic Scope RAG - Consulting Intelligence",
  description: "Production-grade RAG system for technology and strategy consulting",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <div className="flex h-screen bg-[#1a1b1e]">
          <IconSidebar />
          <main className="flex-1 overflow-hidden">
            {children}
          </main>
        </div>
      </body>
    </html>
  );
}
