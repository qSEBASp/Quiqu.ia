"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import { ChevronRight, Search, TriangleAlert } from "lucide-react";
import type { MatchSummary } from "@/lib/types";
import { fmtDate } from "@/lib/format";
import { ANALYZED_MODES, GAME_MODES, modeInfo } from "@/lib/modes";
import { ResultBadge } from "./ResultBadge";
import { severityInfo } from "./severity";
import { clsx } from "./clsx";

type Filter = "all" | "win" | "loss";

export function MatchesTable({ matches }: { matches: MatchSummary[] }) {
  const [filter, setFilter] = useState<Filter>("all");
  const [mode, setMode] = useState("all");
  const [map, setMap] = useState("all");
  const [query, setQuery] = useState("");

  const maps = useMemo(
    () => Array.from(new Set(matches.map((m) => m.map))).sort(),
    [matches],
  );

  const modeOptions = useMemo(() => {
    const counts = new Map<string, { id: string; label: string; count: number }>();
    for (const match of matches) {
      const info = modeInfo(match.mode);
      const entry = counts.get(info.id) ?? { ...info, count: 0 };
      entry.count += 1;
      counts.set(info.id, entry);
    }
    const known = ANALYZED_MODES.map(
      (item) => counts.get(item.id) ?? { id: item.id, label: item.label, count: 0 },
    );
    const extras = Array.from(counts.values())
      .filter((entry) => !GAME_MODES.some((item) => item.id === entry.id))
      .sort((a, b) => a.label.localeCompare(b.label));
    return [...known, ...extras];
  }, [matches]);

  const filtered = useMemo(() => {
    return matches.filter((match) => {
      if (filter !== "all" && match.result !== filter) return false;
      if (mode !== "all" && modeInfo(match.mode).id !== mode) return false;
      if (map !== "all" && match.map !== map) return false;
      if (query) {
        const needle = query.toLowerCase();
        if (
          !match.map.toLowerCase().includes(needle) &&
          !match.agent.toLowerCase().includes(needle)
        ) {
          return false;
        }
      }
      return true;
    });
  }, [matches, filter, mode, map, query]);

  const selectedModeLabel = modeOptions.find((item) => item.id === mode)?.label;

  return (
    <div>
      <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex rounded-xl border border-white/5 bg-white/[0.02] p-1">
          {(
            [
              ["all", "Todas"],
              ["win", "Victorias"],
              ["loss", "Derrotas"],
            ] as const
          ).map(([value, label]) => (
            <button
              key={value}
              type="button"
              onClick={() => setFilter(value)}
              className={clsx(
                "rounded-lg px-3 py-1.5 text-xs font-medium transition",
                filter === value
                  ? "bg-white/[0.08] text-white"
                  : "text-white/40 hover:text-white/70",
              )}
            >
              {label}
            </button>
          ))}
        </div>

        <div className="flex items-center gap-2">
          <div className="relative">
            <Search
              size={13}
              className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-white/25"
            />
            <input
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Mapa o agente"
              className="h-9 w-40 rounded-lg border border-white/5 bg-white/[0.02] pl-8 pr-3 text-xs text-white/80 outline-none transition placeholder:text-white/25 focus:border-brand-500/40"
            />
          </div>
          <select
            value={map}
            onChange={(event) => setMap(event.target.value)}
            className="h-9 rounded-lg border border-white/5 bg-ink-850 px-2.5 text-xs text-white/70 outline-none focus:border-brand-500/40"
          >
            <option value="all">Todos los mapas</option>
            {maps.map((name) => (
              <option key={name} value={name}>
                {name}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div className="mb-5">
        <div className="flex flex-wrap items-center gap-1.5">
          <span className="mr-1 text-[9px] uppercase tracking-[0.14em] text-white/25">
            Tipo de partida
          </span>
          <button
            type="button"
            onClick={() => setMode("all")}
            className={clsx(
              "inline-flex items-center rounded-lg border px-2.5 py-1.5 text-[11px] font-medium transition",
              mode === "all"
                ? "border-brand-500/40 bg-brand-500/15 text-white"
                : "border-white/5 bg-white/[0.02] text-white/45 hover:border-white/10 hover:text-white/75",
            )}
          >
            Todos
            <span className="num ml-1.5 text-[10px] opacity-60">{matches.length}</span>
          </button>
          {modeOptions.map((option) => (
            <button
              key={option.id}
              type="button"
              title={GAME_MODES.find((item) => item.id === option.id)?.hint}
              onClick={() => setMode(option.id)}
              className={clsx(
                "inline-flex items-center rounded-lg border px-2.5 py-1.5 text-[11px] font-medium transition",
                mode === option.id
                  ? "border-brand-500/40 bg-brand-500/15 text-white"
                  : "border-white/5 bg-white/[0.02] text-white/45 hover:border-white/10 hover:text-white/75",
              )}
            >
              {option.label}
              <span className="num ml-1.5 text-[10px] opacity-60">{option.count}</span>
            </button>
          ))}
        </div>
        <p className="mt-2 text-[10px] leading-relaxed text-white/25">
          Solo se analizan los modos con rondas. Deathmatch, Team Deathmatch,
          Escalation y Custom no se guardan en el historial.
        </p>
      </div>

      <div className="panel overflow-hidden">
        <div className="hidden grid-cols-[1.6fr_1fr_0.9fr_0.7fr_0.7fr_0.7fr_24px] gap-3 border-b border-white/5 px-5 py-3 text-[10px] uppercase tracking-[0.14em] text-white/25 md:grid">
          <span>Partida</span>
          <span>Resultado</span>
          <span>KDA</span>
          <span>ACS</span>
          <span>HS%</span>
          <span>KAST</span>
          <span />
        </div>

        {filtered.length === 0 && (
          <p className="px-5 py-10 text-center text-xs text-white/35">
            {mode !== "all"
              ? `Todavía no hay partidas de ${selectedModeLabel ?? "ese modo"}.`
              : "No hay partidas con esos filtros."}
          </p>
        )}

        <ul className="divide-y divide-white/5">
          {filtered.map((match) => {
            const severity = severityInfo(match.top_insight_severity ?? 1);
            return (
              <li key={match.id}>
                <Link
                  href={`/matches/${match.id}`}
                  className="group grid gap-3 px-5 py-3.5 transition hover:bg-white/[0.025] md:grid-cols-[1.6fr_1fr_0.9fr_0.7fr_0.7fr_0.7fr_24px] md:items-center"
                >
                  <div className="flex items-center gap-3">
                    <span
                      className={clsx(
                        "h-9 w-1 shrink-0 rounded-full",
                        match.result === "win" ? "bg-mint-500/70" : "bg-brand-500/70",
                      )}
                    />
                    <div className="min-w-0">
                      <p className="truncate text-sm font-medium text-white/90">
                        {match.map}
                        <span className="ml-2 text-[11px] font-normal text-white/35">
                          {match.agent}
                        </span>
                      </p>
                      <p className="mt-0.5 text-[10px] text-white/30">
                        {fmtDate(match.started_at)} · {modeInfo(match.mode).label}
                      </p>
                    </div>
                  </div>

                  <div>
                    <ResultBadge
                      result={match.result}
                      score={`${match.score_us}-${match.score_them}`}
                      size="sm"
                    />
                  </div>

                  <div className="flex items-center gap-3 md:contents">
                    <span className="num text-xs text-white/65">
                      {match.kills}/{match.deaths}/{match.assists}
                    </span>
                    <span className="num text-xs text-white/70">{match.acs.toFixed(0)}</span>
                    <span className="num text-xs text-white/55">
                      {match.hs_pct.toFixed(0)}%
                    </span>
                    <span className="num text-xs text-white/55">
                      {match.kast.toFixed(0)}%
                    </span>
                  </div>

                  <ChevronRight
                    size={15}
                    className="hidden text-white/20 transition group-hover:text-brand-400 md:block"
                  />

                  <div className="rounded-lg border border-white/5 bg-white/[0.015] px-3 py-2 md:col-span-7">
                    {match.top_insight ? (
                      <div className="flex items-start gap-2.5">
                        <TriangleAlert
                          size={12}
                          className={clsx("mt-0.5 shrink-0", severity.text)}
                        />
                        <div className="min-w-0">
                          <p className="text-[11px] leading-snug text-white/45">
                            <span className="mr-1 text-[9px] uppercase tracking-[0.12em] text-white/25">
                              A corregir
                            </span>
                            <span className="font-medium text-white/80">
                              {match.top_insight}
                            </span>
                          </p>
                          {match.top_fix && (
                            <p className="mt-1 line-clamp-2 text-[10px] leading-relaxed text-white/35">
                              {match.top_fix}
                            </p>
                          )}
                        </div>
                        <span
                          className={clsx(
                            "ml-auto hidden shrink-0 rounded-md border px-1.5 py-0.5 text-[9px] font-medium uppercase tracking-[0.1em] sm:inline-flex",
                            severity.badge,
                          )}
                        >
                          {severity.label}
                        </span>
                      </div>
                    ) : (
                      <p className="text-[11px] text-mint-400/80">
                        Sin errores graves en esta partida. Mantén el nivel.
                      </p>
                    )}
                  </div>
                </Link>
              </li>
            );
          })}
        </ul>
      </div>
      <p className="mt-3 text-[10px] text-white/25">
        {filtered.length} de {matches.length} partidas
      </p>
    </div>
  );
}
