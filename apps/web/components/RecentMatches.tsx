import Link from "next/link";
import { ArrowUpRight, ChevronRight } from "lucide-react";
import type { MatchSummary } from "@/lib/types";
import { fmtDate } from "@/lib/format";
import { ResultBadge } from "./ResultBadge";
import { clsx } from "./clsx";

export function RecentMatches({ matches }: { matches: MatchSummary[] }) {
  return (
    <section className="panel overflow-hidden">
      <div className="flex items-center justify-between border-b border-white/5 px-5 py-4">
        <div>
          <h2 className="text-sm font-semibold tracking-tight">Partidas recientes</h2>
          <p className="mt-0.5 text-[11px] text-white/35">Últimos resultados analizados.</p>
        </div>
        <Link
          href="/matches"
          className="inline-flex items-center gap-1 text-[11px] font-medium text-white/45 transition hover:text-white"
        >
          Ver todas
          <ArrowUpRight size={13} />
        </Link>
      </div>

      <ul className="divide-y divide-white/5">
        {matches.map((match) => (
          <li key={match.id}>
            <Link
              href={`/matches/${match.id}`}
              className="group flex items-center gap-3 px-5 py-3 transition hover:bg-white/[0.025] sm:gap-4"
            >
              <span
                className={clsx(
                  "h-8 w-1 shrink-0 rounded-full",
                  match.result === "win" ? "bg-mint-500/70" : "bg-brand-500/70",
                )}
              />
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm font-medium text-white/85">
                  {match.map}
                  <span className="ml-2 text-[11px] font-normal text-white/35">
                    {match.agent}
                  </span>
                </p>
                <p className="mt-0.5 text-[10px] text-white/30">
                  {fmtDate(match.started_at)}
                </p>
              </div>
              <div className="hidden w-20 sm:block">
                <ResultBadge
                  result={match.result}
                  score={`${match.score_us}-${match.score_them}`}
                  size="sm"
                />
              </div>
              <div className="hidden text-right sm:block">
                <p className="num text-xs text-white/65">
                  {match.kills}/{match.deaths}/{match.assists}
                </p>
                <p className="text-[9px] uppercase tracking-[0.12em] text-white/25">KDA</p>
              </div>
              <div className="w-12 text-right">
                <p className="num text-sm font-medium text-white/80">
                  {match.acs.toFixed(0)}
                </p>
                <p className="text-[9px] uppercase tracking-[0.12em] text-white/25">ACS</p>
              </div>
              <ChevronRight
                size={15}
                className="text-white/15 transition group-hover:text-brand-400"
              />
            </Link>
          </li>
        ))}
      </ul>
    </section>
  );
}
