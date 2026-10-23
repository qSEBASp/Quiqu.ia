import { CheckCircle2, ListChecks, Sparkles, Wrench } from "lucide-react";
import type { Report } from "@/lib/types";
import { AiButton } from "./AiButton";
import { severityInfo } from "./severity";

export function ReportCard({
  matchId,
  report,
  hasKey,
}: {
  matchId: string;
  report: Report | null;
  hasKey: boolean;
}) {
  if (!report) {
    return (
      <section className="panel p-5">
        <p className="text-sm text-white/40">Esta partida no tiene informe todavía.</p>
      </section>
    );
  }

  return (
    <section className="panel relative overflow-hidden p-5 sm:p-6">
      <div className="pointer-events-none absolute -right-20 -top-24 h-64 w-64 rounded-full bg-brand-500/[0.07] blur-3xl" />
      <div className="relative">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div className="flex items-center gap-2.5">
            <span className="grid h-9 w-9 place-items-center rounded-xl bg-brand-500/10 text-brand-400">
              <Sparkles size={16} />
            </span>
            <div>
              <h2 className="text-sm font-semibold tracking-tight">Informe del coach</h2>
              <p className="text-[10px] uppercase tracking-[0.14em] text-white/30">
                {report.model === "rules" ? "Motor de reglas" : `IA · ${report.model}`}
              </p>
            </div>
          </div>
          <AiButton matchId={matchId} hasKey={hasKey} />
        </div>

        <p className="mt-4 max-w-3xl text-sm leading-relaxed text-white/65">
          {report.summary}
        </p>

        {report.priorities.length > 0 && (
          <div className="mt-5 space-y-2.5">
            {report.priorities.map((priority, index) => {
              const severity = priority.severity ?? 3;
              const info = severityInfo(severity);
              return (
                <article
                  key={`${priority.title}-${index}`}
                  className="rounded-xl border border-white/5 bg-white/[0.015] p-4"
                >
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="num text-[10px] text-white/25">
                      0{index + 1}
                    </span>
                    <h3 className="text-[13px] font-semibold text-white/90">
                      {priority.title}
                    </h3>
                    {priority.category && (
                      <span className="rounded-md border border-white/5 bg-white/[0.03] px-1.5 py-0.5 text-[9px] uppercase tracking-[0.1em] text-white/40">
                        {priority.category}
                      </span>
                    )}
                    <span
                      className={`rounded-md border px-1.5 py-0.5 text-[9px] font-medium uppercase tracking-[0.1em] ${info.badge}`}
                    >
                      {info.label}
                    </span>
                  </div>
                  <p className="mt-2 text-xs leading-relaxed text-white/50">
                    {priority.why}
                  </p>
                  <div className="mt-2.5 flex items-start gap-2 rounded-lg border border-mint-500/10 bg-mint-500/[0.04] px-3 py-2">
                    <Wrench size={12} className="mt-0.5 shrink-0 text-mint-400" />
                    <p className="text-xs leading-relaxed text-mint-400/90">
                      {priority.fix}
                    </p>
                  </div>
                </article>
              );
            })}
          </div>
        )}

        {report.drills.length > 0 && (
          <div className="mt-5">
            <div className="flex items-center gap-2">
              <ListChecks size={13} className="text-white/40" />
              <p className="label-xs">Plan de práctica</p>
            </div>
            <ul className="mt-2.5 grid gap-2 sm:grid-cols-3">
              {report.drills.map((drill, index) => (
                <li
                  key={`${drill}-${index}`}
                  className="flex items-start gap-2 rounded-xl border border-white/5 bg-white/[0.015] p-3"
                >
                  <CheckCircle2 size={13} className="mt-0.5 shrink-0 text-mint-400" />
                  <span className="text-[11px] leading-relaxed text-white/55">{drill}</span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </section>
  );
}
