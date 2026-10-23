import Link from "next/link";
import { Activity, ArrowUpRight, Flame } from "lucide-react";
import { AccountSwitcher } from "@/components/AccountSwitcher";
import { EmptyDashboard } from "@/components/EmptyDashboard";
import { OfflineNotice } from "@/components/OfflineNotice";
import { PageHeader } from "@/components/PageHeader";
import { PatternsList } from "@/components/PatternsList";
import { RecentMatches } from "@/components/RecentMatches";
import { StatCard } from "@/components/StatCard";
import { StrengthCard } from "@/components/StrengthCard";
import { SyncButton } from "@/components/SyncButton";
import { TrendChart } from "@/components/TrendChart";
import { WinrateRing } from "@/components/WinrateRing";
import { fetchOverview } from "@/lib/server";
import { pct } from "@/lib/format";

export const dynamic = "force-dynamic";

export default async function DashboardPage() {
  const overview = await fetchOverview();
  if (!overview) return <OfflineNotice />;
  if (overview.totals.matches === 0) {
    return <EmptyDashboard profile={overview.profile} />;
  }

  const totals = overview.totals;
  const strengths = overview.strengths ?? [];
  const streak =
    totals.current_streak > 0
      ? `${totals.current_streak} ${totals.streak_result === "win" ? "victorias" : "derrotas"} seguidas`
      : "Sin racha activa";

  return (
    <div className="rise-in">
      <PageHeader
        eyebrow="Resumen"
        title={`Hola, ${overview.profile.riot_id}`}
        description={`${totals.matches} partidas analizadas · ${totals.wins} victorias y ${totals.losses} derrotas. Tu forma media es ${totals.form_score.toFixed(0)}/100.`}
        actions={
          <div className="flex flex-wrap items-center gap-2">
            <AccountSwitcher profile={overview.profile} />
            <SyncButton />
          </div>
        }
      />

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <div className="panel flex items-center gap-4 p-4 sm:p-5">
          <WinrateRing
            winrate={totals.winrate}
            wins={totals.wins}
            losses={totals.losses}
          />
          <div>
            <p className="label-xs">Winrate</p>
            <p className="mt-2 text-sm font-medium text-white/80">
              {totals.wins}V · {totals.losses}D
            </p>
            <p className="mt-1 flex items-center gap-1.5 text-[11px] text-white/35">
              <Flame size={11} className="text-brand-400" />
              {streak}
            </p>
          </div>
        </div>

        <StatCard
          label="ACS"
          value={totals.acs.toFixed(0)}
          description="Impacto medio por ronda"
          tone="brand"
        />
        <StatCard
          label="KAST"
          value={pct(totals.kast)}
          description="Rondas con impacto o supervivencia"
          tone="mint"
        />
        <StatCard
          label="K/D"
          value={totals.kd.toFixed(2)}
          description={`${totals.kills} kills · ${totals.deaths} deaths`}
          tone="sky"
        />
      </div>

      <div className="mt-4 grid gap-4 xl:grid-cols-[1.7fr_1fr]">
        <section className="panel p-5">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div>
              <h2 className="text-sm font-semibold tracking-tight">Evolución de ACS</h2>
              <p className="mt-0.5 text-[11px] text-white/35">
                Tus últimas {overview.trend.length} partidas.
              </p>
            </div>
            <div className="flex items-center gap-1.5 rounded-lg border border-white/5 bg-white/[0.02] px-2.5 py-1 text-[10px] text-white/40">
              <Activity size={11} className="text-mint-400" />
              Media {totals.acs.toFixed(0)} ACS
            </div>
          </div>
          <div className="mt-3">
            <TrendChart points={overview.trend} />
          </div>
          <div className="mt-2 flex flex-wrap items-center gap-4 border-t border-white/5 pt-3 text-[10px] text-white/35">
            <span>
              ADR <span className="num text-white/60">{totals.adr.toFixed(0)}</span>
            </span>
            <span>
              HS <span className="num text-white/60">{pct(totals.hs_pct, 1)}</span>
            </span>
            <span>
              Forma <span className="num text-white/60">{totals.form_score.toFixed(0)}</span>
            </span>
            <Link
              href="/matches"
              className="ml-auto inline-flex items-center gap-1 text-white/45 transition hover:text-white"
            >
              Historial completo <ArrowUpRight size={11} />
            </Link>
          </div>
        </section>

        <section className="panel p-5">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-sm font-semibold tracking-tight">Patrones recurrentes</h2>
              <p className="mt-0.5 text-[11px] text-white/35">
                Lo que más se repite en tu historial.
              </p>
            </div>
          </div>
          <div className="mt-3">
            <PatternsList patterns={overview.top_patterns} />
          </div>
        </section>
      </div>

      <section className="mt-6">
        <div className="mb-3 flex flex-wrap items-end justify-between gap-2">
          <div>
            <p className="label-xs">Puntos fuertes</p>
            <h2 className="mt-1 text-lg font-semibold tracking-tight">
              Lo que estás haciendo bien
            </h2>
            <p className="mt-0.5 text-[11px] text-white/35">
              Lo que ya funciona en tu juego y conviene mantener.
            </p>
          </div>
          {strengths.length > 0 && (
            <span className="num text-[11px] text-white/30">
              {strengths.length} señales positivas
            </span>
          )}
        </div>
        {strengths.length > 0 ? (
          <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
            {strengths.slice(0, 3).map((strength) => (
              <StrengthCard
                key={strength.rule_id}
                strength={strength}
                count={strength.count}
              />
            ))}
          </div>
        ) : (
          <div className="rounded-xl border border-dashed border-white/10 bg-white/[0.01] p-5 text-xs leading-relaxed text-white/40">
            Todavía no hay suficientes partidas con datos suficientes para
            confirmar tus puntos fuertes. Sigue sincronizando y aquí verás lo que
            ya estás haciendo bien.
          </div>
        )}
      </section>

      <div className="mt-4">
        <RecentMatches matches={overview.recent} />
      </div>
    </div>
  );
}
