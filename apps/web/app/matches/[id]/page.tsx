import Link from "next/link";
import { ArrowLeft, Clock, MapPin, SearchX } from "lucide-react";
import { InsightCard } from "@/components/InsightCard";
import { MetricGrid } from "@/components/MetricGrid";
import { OfflineNotice } from "@/components/OfflineNotice";
import { ReportCard } from "@/components/ReportCard";
import { ResultBadge } from "@/components/ResultBadge";
import { RoundTimeline } from "@/components/RoundTimeline";
import { Scoreboard } from "@/components/Scoreboard";
import { StrengthCard } from "@/components/StrengthCard";
import { fetchMatch, fetchProfile } from "@/lib/server";
import { fmtDate } from "@/lib/format";
import { modeInfo } from "@/lib/modes";

export const dynamic = "force-dynamic";

export default async function MatchPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const [match, profile] = await Promise.all([fetchMatch(id), fetchProfile()]);

  if (!profile) return <OfflineNotice />;

  if (!match) {
    return (
      <div className="panel mx-auto mt-10 max-w-md p-8 text-center">
        <span className="mx-auto grid h-11 w-11 place-items-center rounded-xl bg-white/[0.04] text-white/40">
          <SearchX size={19} />
        </span>
        <h1 className="mt-4 text-lg font-semibold">Partida no encontrada</h1>
        <p className="mt-1 text-xs text-white/40">
          Puede que se haya borrado al cambiar de cuenta o al borrar el historial.
        </p>
        <Link
          href="/matches"
          className="mt-5 inline-flex items-center gap-1.5 text-xs font-medium text-brand-400 hover:text-brand-500"
        >
          <ArrowLeft size={13} /> Volver a las partidas
        </Link>
      </div>
    );
  }

  const metrics = match.metrics;
  const strengths = match.strengths ?? [];

  return (
    <div className="rise-in">
      <Link
        href="/matches"
        className="inline-flex items-center gap-1.5 text-[11px] font-medium text-white/35 transition hover:text-white"
      >
        <ArrowLeft size={13} />
        Volver a partidas
      </Link>

      <header className="mt-4 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <div className="flex flex-wrap items-center gap-2 text-[10px] text-white/35">
            <span className="rounded-md border border-white/5 bg-white/[0.03] px-1.5 py-0.5 uppercase tracking-[0.12em]">
              {modeInfo(match.mode).label}
            </span>
            <span className="inline-flex items-center gap-1">
              <Clock size={10} /> {fmtDate(match.started_at)}
            </span>
            <span className="inline-flex items-center gap-1">
              <MapPin size={10} /> {match.map}
            </span>
            {match.source === "demo" && (
              <span className="rounded-md border border-amber-400/20 bg-amber-400/[0.06] px-1.5 py-0.5 text-amber-400">
                DEMO
              </span>
            )}
          </div>
          <h1 className="mt-2 text-3xl font-semibold tracking-[-0.03em] sm:text-[34px]">
            {match.map}
            <span className="mx-2 text-white/15">·</span>
            <span className="text-white/70">{match.agent}</span>
          </h1>
          <div className="mt-3 flex items-center gap-3">
            <ResultBadge result={match.result} />
            <span className="num text-2xl font-semibold tracking-tight text-white/90">
              {match.score_us}
              <span className="mx-1 text-white/20">:</span>
              {match.score_them}
            </span>
          </div>
        </div>

        <div className="grid grid-cols-3 gap-2 sm:gap-3">
          <div className="panel px-3 py-2 text-right">
            <p className="num text-lg font-semibold text-white/85">
              {match.kills}/{match.deaths}/{match.assists}
            </p>
            <p className="text-[9px] uppercase tracking-[0.14em] text-white/30">KDA</p>
          </div>
          <div className="panel px-3 py-2 text-right">
            <p className="num text-lg font-semibold text-brand-400">
              {metrics.acs.toFixed(0)}
            </p>
            <p className="text-[9px] uppercase tracking-[0.14em] text-white/30">ACS</p>
          </div>
          <div className="panel px-3 py-2 text-right">
            <p className="num text-lg font-semibold text-mint-400">
              {metrics.form_score.toFixed(0)}
            </p>
            <p className="text-[9px] uppercase tracking-[0.14em] text-white/30">Forma</p>
          </div>
        </div>
      </header>

      <div className="mt-6">
        <ReportCard
          matchId={match.id}
          report={match.report}
          hasKey={profile.has_llm_key}
        />
      </div>

      {strengths.length > 0 && (
        <section className="mt-6">
          <div className="mb-3 flex items-end justify-between">
            <div>
              <p className="label-xs">Puntos fuertes</p>
              <h2 className="mt-1 text-lg font-semibold tracking-tight">
                Lo que hiciste bien
              </h2>
            </div>
            <span className="num text-[11px] text-white/30">
              {strengths.length} señales
            </span>
          </div>
          <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
            {strengths.map((strength) => (
              <StrengthCard key={strength.rule_id} strength={strength} />
            ))}
          </div>
        </section>
      )}

      <section className="panel mt-4 p-5">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-sm font-semibold tracking-tight">Métricas de la partida</h2>
            <p className="mt-0.5 text-[11px] text-white/35">
              {metrics.rounds} rondas · {metrics.attack_rounds} de ataque ·{" "}
              {metrics.defense_rounds} de defensa
            </p>
          </div>
        </div>
        <div className="mt-3">
          <MetricGrid metrics={metrics} />
        </div>
      </section>

      <div className="mt-4">
        <RoundTimeline rounds={match.rounds} />
      </div>

      {match.insights.length > 0 && (
        <section className="mt-6">
          <div className="mb-3 flex items-end justify-between">
            <div>
              <p className="label-xs">Diagnóstico</p>
              <h2 className="mt-1 text-lg font-semibold tracking-tight">
                Errores detectados
              </h2>
            </div>
            <span className="num text-[11px] text-white/30">
              {match.insights.length} hallazgos
            </span>
          </div>
          <div className="grid gap-3 md:grid-cols-2">
            {match.insights.map((insight) => (
              <InsightCard key={insight.id} insight={insight} />
            ))}
          </div>
        </section>
      )}

      <div className="mt-6">
        <Scoreboard entries={match.scoreboard} />
      </div>
    </div>
  );
}
