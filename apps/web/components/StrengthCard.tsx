import { Sparkles } from "lucide-react";
import type { Strength } from "@/lib/types";

function metricText(value: number): string {
  return Number.isInteger(value) ? value.toFixed(0) : value.toFixed(1);
}

export function StrengthCard({
  strength,
  count,
}: {
  strength: Strength;
  count?: number;
}) {
  return (
    <article className="panel relative overflow-hidden p-4">
      <span className="absolute inset-y-0 left-0 w-[3px] bg-mint-500/70" />
      <div className="flex items-start justify-between gap-3 pl-1.5">
        <div className="flex flex-wrap items-center gap-2">
          <span className="rounded-md border border-white/5 bg-white/[0.03] px-1.5 py-0.5 text-[9px] uppercase tracking-[0.12em] text-white/40">
            {strength.category}
          </span>
          <span className="rounded-md border border-mint-500/25 bg-mint-500/10 px-1.5 py-0.5 text-[9px] font-medium uppercase tracking-[0.1em] text-mint-400">
            Punto fuerte
          </span>
        </div>
        {count !== undefined ? (
          <span className="num shrink-0 rounded border border-mint-500/15 bg-mint-500/[0.06] px-1.5 py-0.5 text-[9px] text-mint-400/80">
            {count}×
          </span>
        ) : (
          strength.metric !== null && (
            <span className="num shrink-0 text-[10px] text-white/30">
              {metricText(strength.metric)}
            </span>
          )
        )}
      </div>

      <h3 className="mt-2.5 pl-1.5 text-[13px] font-semibold text-white/90">
        {strength.title}
      </h3>
      <p className="mt-1.5 pl-1.5 text-xs leading-relaxed text-white/45">
        {count !== undefined ? strength.summary : strength.detail}
      </p>

      <div className="mt-3 ml-1.5 flex items-center gap-1.5 text-[10px] text-mint-400/70">
        <Sparkles size={11} />
        <span>
          {count !== undefined ? "Se repite en tu historial" : "Mantenlo"}
        </span>
      </div>
    </article>
  );
}
