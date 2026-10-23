"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Crosshair,
  LayoutDashboard,
  Settings,
  Swords,
} from "lucide-react";
import { clsx } from "./clsx";

const items = [
  { href: "/", label: "Resumen", icon: LayoutDashboard },
  { href: "/matches", label: "Partidas", icon: Swords },
  { href: "/settings", label: "Ajustes", icon: Settings },
];

function active(pathname: string, href: string): boolean {
  if (href === "/") return pathname === "/";
  return pathname.startsWith(href);
}

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="fixed inset-y-0 left-0 z-30 hidden w-[248px] flex-col border-r border-white/5 bg-ink-950/85 px-5 py-6 backdrop-blur-xl lg:flex">
      <Link href="/" className="flex items-center gap-3 px-2">
        <span className="grid h-10 w-10 place-items-center rounded-xl bg-brand-500 font-black text-white shadow-[0_0_28px_rgba(255,70,85,0.35)]">
          Q
        </span>
        <span>
          <span className="block text-sm font-bold tracking-[0.18em]">QUIQU.IA</span>
          <span className="block text-[10px] uppercase tracking-[0.22em] text-white/35">
            Valorant coach
          </span>
        </span>
      </Link>

      <nav className="mt-10 space-y-1">
        {items.map((item) => {
          const Icon = item.icon;
          const isActive = active(pathname, item.href);
          return (
            <Link
              key={item.href}
              href={item.href}
              className={clsx(
                "group flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm transition",
                isActive
                  ? "bg-white/[0.06] text-white"
                  : "text-white/50 hover:bg-white/[0.035] hover:text-white/85",
              )}
            >
              <Icon
                size={17}
                className={clsx(
                  "transition",
                  isActive ? "text-brand-400" : "text-white/35 group-hover:text-white/70",
                )}
              />
              <span className="font-medium">{item.label}</span>
              {isActive && (
                <span className="ml-auto h-1.5 w-1.5 rounded-full bg-brand-500" />
              )}
            </Link>
          );
        })}
      </nav>

      <div className="mt-auto space-y-3">
        <div className="rounded-xl border border-white/5 bg-white/[0.02] p-3">
          <div className="flex items-center gap-2">
            <Crosshair size={14} className="text-mint-400" />
            <p className="label-xs !tracking-[0.12em]">Entorno local</p>
          </div>
          <p className="mt-1.5 text-[11px] leading-relaxed text-white/40">
            Tus datos y vídeos se quedan en tu PC. Nada se sube a un servidor externo.
          </p>
        </div>
        <p className="px-2 text-[10px] uppercase tracking-[0.2em] text-white/20">
          v0.1 · MVP
        </p>
      </div>
    </aside>
  );
}

export function MobileNav() {
  const pathname = usePathname();

  return (
    <div className="sticky top-0 z-30 flex items-center justify-between border-b border-white/5 bg-ink-950/90 px-4 py-3 backdrop-blur-xl lg:hidden">
      <Link href="/" className="flex items-center gap-2.5">
        <span className="grid h-8 w-8 place-items-center rounded-lg bg-brand-500 text-sm font-black">
          Q
        </span>
        <span className="text-xs font-bold tracking-[0.16em]">QUIQU.IA</span>
      </Link>
      <nav className="flex items-center gap-1">
        {items.map((item) => {
          const Icon = item.icon;
          const isActive = active(pathname, item.href);
          return (
            <Link
              key={item.href}
              href={item.href}
              aria-label={item.label}
              className={clsx(
                "grid h-9 w-9 place-items-center rounded-lg transition",
                isActive
                  ? "bg-white/[0.08] text-brand-400"
                  : "text-white/45 hover:text-white",
              )}
            >
              <Icon size={17} />
            </Link>
          );
        })}
      </nav>
    </div>
  );
}
