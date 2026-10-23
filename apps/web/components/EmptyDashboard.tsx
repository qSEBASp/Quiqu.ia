import { ArrowRight, BarChart3, DatabaseZap, ScanEye } from "lucide-react";
import type { Profile } from "@/lib/types";
import { AccountSwitcher } from "./AccountSwitcher";
import { SyncButton } from "./SyncButton";

const steps = [
  {
    icon: DatabaseZap,
    title: "Carga tus partidas",
    body: "Sincroniza las últimas partidas desde Riot. En demo se generan 14 partidas realistas para probar todo.",
  },
  {
    icon: ScanEye,
    title: "Detección de errores",
    body: "El motor cruza rondas, economía, trades, utilidad y primeros contactos para encontrar patrones.",
  },
  {
    icon: BarChart3,
    title: "Informe accionable",
    body: "Recibes las prioridades de la partida con evidencia por ronda y un plan de práctica concreto.",
  },
];

export function EmptyDashboard({ profile }: { profile: Profile }) {
  return (
    <div className="rise-in">
      <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
        <p className="label-xs">Cuenta</p>
        <AccountSwitcher profile={profile} />
      </div>

      <div className="panel relative overflow-hidden p-6 sm:p-10">
        <div className="pointer-events-none absolute -right-24 -top-24 h-72 w-72 rounded-full bg-brand-500/10 blur-3xl" />
        <div className="relative max-w-2xl">
          <p className="label-xs">Primer paso</p>
          <h1 className="mt-3 text-3xl font-semibold tracking-[-0.03em] sm:text-4xl">
            Tu coach personal de Valorant.
          </h1>
          <p className="mt-4 text-sm leading-relaxed text-white/50">
            Hola {profile.riot_id}#{profile.tag}. Todavía no hay partidas analizadas.
            Sincroniza tu historial para ver el analizador en acción.
          </p>
          <div className="mt-6 flex flex-wrap items-center gap-3">
            <SyncButton label="Sincronizar partidas" size="lg" />
            <a
              href="/settings"
              className="inline-flex items-center gap-2 rounded-xl border border-white/10 px-4 py-3 text-sm font-medium text-white/70 transition hover:border-white/20 hover:text-white"
            >
              Conectar mi cuenta
              <ArrowRight size={15} />
            </a>
          </div>
          <p className="mt-4 text-[11px] text-white/30">
            Modo actual:{" "}
            {profile.provider === "demo" ? "demo local" : "HenrikDev (Riot)"} ·{" "}
            {profile.region.toUpperCase()}
          </p>
        </div>
      </div>

      <div className="mt-4 grid gap-4 sm:grid-cols-3">
        {steps.map((step, index) => {
          const Icon = step.icon;
          return (
            <div key={step.title} className="panel p-5">
              <div className="flex items-center justify-between">
                <span className="grid h-9 w-9 place-items-center rounded-lg bg-white/[0.04] text-white/60">
                  <Icon size={16} />
                </span>
                <span className="num text-xs text-white/20">0{index + 1}</span>
              </div>
              <h2 className="mt-4 text-sm font-semibold">{step.title}</h2>
              <p className="mt-1.5 text-xs leading-relaxed text-white/40">{step.body}</p>
            </div>
          );
        })}
      </div>
    </div>
  );
}
