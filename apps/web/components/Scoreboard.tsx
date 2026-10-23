import type { ScoreboardEntry } from "@/lib/types";
import { clsx } from "./clsx";

export function Scoreboard({ entries }: { entries: ScoreboardEntry[] }) {
  if (entries.length === 0) {
    return null;
  }
  const sorted = [...entries].sort((a, b) => b.acs - a.acs);
  const maxAcs = Math.max(...sorted.map((e) => e.acs), 1);

  return (
    <section className="panel overflow-hidden">
      <div className="border-b border-white/5 px-5 py-4">
        <h2 className="text-sm font-semibold tracking-tight">Tabla de puntuación</h2>
        <p className="mt-0.5 text-[11px] text-white/35">Ordenada por ACS de la partida.</p>
      </div>
      <div className="grid grid-cols-[1.7fr_0.9fr_0.8fr_0.8fr] gap-3 border-b border-white/5 px-5 py-2.5 text-[9px] uppercase tracking-[0.14em] text-white/25 sm:grid-cols-[1.7fr_0.7fr_0.9fr_0.8fr_1fr]">
        <span>Jugador</span>
        <span>Agente</span>
        <span className="text-right">K/D/A</span>
        <span className="hidden text-right sm:block">ACS</span>
        <span className="hidden text-right sm:block">Impacto</span>
      </div>
      <ul className="divide-y divide-white/5">
        {sorted.map((entry) => (
          <li
            key={`${entry.name}-${entry.tag}-${entry.team}`}
            className={clsx(
              "grid grid-cols-[1.7fr_0.9fr_0.8fr_0.8fr] items-center gap-3 px-5 py-2.5 sm:grid-cols-[1.7fr_0.7fr_0.9fr_0.8fr_1fr]",
              entry.is_me && "bg-brand-500/[0.05]",
            )}
          >
            <div className="flex min-w-0 items-center gap-2">
              <span
                className={clsx(
                  "h-1.5 w-1.5 shrink-0 rounded-full",
                  entry.team === "Blue" ? "bg-sky-400/70" : "bg-brand-500/70",
                )}
              />
              <span
                className={clsx(
                  "truncate text-xs",
                  entry.is_me ? "font-semibold text-white" : "text-white/65",
                )}
              >
                {entry.name}
                <span className="text-white/25">#{entry.tag}</span>
              </span>
              {entry.is_me && (
                <span className="rounded border border-brand-500/20 bg-brand-500/10 px-1 py-0.5 text-[8px] font-semibold uppercase tracking-[0.1em] text-brand-400">
                  Tú
                </span>
              )}
            </div>
            <span className="truncate text-[11px] text-white/40">{entry.agent}</span>
            <span className="num text-right text-[11px] text-white/55">
              {entry.kills}/{entry.deaths}/{entry.assists}
            </span>
            <span className="num hidden text-right text-[11px] text-white/65 sm:block">
              {entry.acs.toFixed(0)}
            </span>
            <div className="hidden justify-end sm:flex">
              <div className="h-1 w-full max-w-[80px] overflow-hidden rounded-full bg-white/[0.05]">
                <div
                  className={clsx(
                    "h-full rounded-full",
                    entry.is_me ? "bg-brand-500" : "bg-white/20",
                  )}
                  style={{ width: `${Math.max(6, (entry.acs / maxAcs) * 100)}%` }}
                />
              </div>
            </div>
          </li>
        ))}
      </ul>
    </section>
  );
}
