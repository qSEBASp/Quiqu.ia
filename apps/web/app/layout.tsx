import type { Metadata } from "next";
import type { ReactNode } from "react";
import "./globals.css";
import { MobileNav, Sidebar } from "@/components/Sidebar";

export const metadata: Metadata = {
  title: "quiqu.ia · Coach de Valorant",
  description:
    "Analiza tus partidas de Valorant, detecta errores repetidos y recibe un plan de mejora.",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="es">
      <body className="min-h-screen antialiased">
        <Sidebar />
        <MobileNav />
        <div className="lg:pl-[248px]">
          <main className="mx-auto w-full max-w-[1240px] px-4 pb-20 pt-6 sm:px-6 lg:px-10 lg:pt-10">
            {children}
          </main>
        </div>
      </body>
    </html>
  );
}
