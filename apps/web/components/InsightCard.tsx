import { ArrowRight, CircleAlert } from "lucide-react";
import type { Insight } from "@/lib/types";
import { severityInfo } from "./severity";

export function InsightCard({ insight }: { insight: Insight }) {
  const info = severityInfo(insight.severity);
  const rounds = (insight.evidence?.rounds as number[] | undefined) ?? [];

  return (
    <article className="panel relative overflow-hidden p-4">
      <span className={`absolute inset-y-0 left-0 w-[3px] ${info.bar}`} />
      <div className="flex items-start justify-between gap-3 pl-1.5">
        <div className="flex flex-wrap items-center gap-2">
          <span className="rounded-md border border-white/5 bg-white/[0.03] px-1.5 py-0.5 text-[9px] uppercase tracking-[0.12em] text-white/40">
            {insight.category}
          </span>
          <span
            className={`rounded-md border px-1.5 py-0.5 text-[9px] font-medium uppercase tracking-[0.1em] ${info.badge}`}
          >
            {info.label}
          </span>
        </div>
        {insight.metric !== null && (
          <span className="num shrink-0 text-[10px] text-white/30">
            {insight.metric.toFixed(1)}
            {insight.threshold !== null ? ` / ${insight.threshold}` : ""}
          </span>
        )}
      </div>

      <h3 className="mt-2.5 pl-1.5 text-[13px] font-semibold text-white/90">
        {insight.title}
      </h3>
      <p className="mt-1.5 pl-1.5 text-xs leading-relaxed text-white/45">{insight.detail}</p>

      <div className="mt-3 ml-1.5 flex items-start gap-2 rounded-lg border border-white/5 bg-white/[0.02] px-3 py-2">
        <ArrowRight size={12} className="mt-0.5 shrink-0 text-brand-400" />
        <p className="text-[11px] leading-relaxed text-white/60">{insight.recommendation}</p>
      </div>

      {rounds.length > 0 && (
        <div className="mt-3 ml-1.5 flex flex-wrap items-center gap-1.5">
          <CircleAlert size={11} className="text-white/25" />
          <span className="text-[9px] uppercase tracking-[0.12em] text-white/25">
            Rondas
          </span>
          {rounds.slice(0, 14).map((round) => (
            <span
              key={round}
              className="num rounded border border-white/5 bg-white/[0.03] px-1.5 py-0.5 text-[9px] text-white/45"
            >
              {round}
            </span>
          ))}
          {rounds.length > 14 && (
            <span className="text-[9px] text-white/25">+{rounds.length - 14}</span>
          )}
        </div>
      )}
    </article>
  );
}
