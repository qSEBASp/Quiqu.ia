import type { Metadata } from "next";
import type { ReactNode } from "react";
import "./globals.css";
import { AccountBackdrop } from "@/components/AccountBackdrop";
import { MotionLayer } from "@/components/MotionLayer";
import { MobileNav, Sidebar } from "@/components/Sidebar";
import { fetchBackdrop } from "@/lib/server";

export const metadata: Metadata = {
  title: "quiqu.ia · Coach de Valorant",
  description:
    "Analiza tus partidas de Valorant, detecta errores repetidos y recibe un plan de mejora.",
};

export default async function RootLayout({ children }: { children: ReactNode }) {
  const backdrop = await fetchBackdrop();
  const shutdownEnabled = Boolean(process.env.QUIQU_STOP_FILE);

  return (
    <html lang="es">
      <body className="min-h-screen antialiased">
        <MotionLayer />
        <AccountBackdrop data={backdrop} />
        <Sidebar shutdownEnabled={shutdownEnabled} />
        <MobileNav shutdownEnabled={shutdownEnabled} />
        <div className="relative z-10 lg:pl-[248px]">
          <main className="mx-auto w-full max-w-[1240px] px-4 pb-20 pt-6 sm:px-6 lg:px-10 lg:pt-10">
            {children}
          </main>
        </div>
      </body>
    </html>
  );
}
