import Link from "next/link";
import { ArrowUpRight } from "lucide-react";
import type { Pattern } from "@/lib/types";
import { clsx } from "./clsx";

export function PatternsList({ patterns }: { patterns: Pattern[] }) {
  if (patterns.length === 0) {
    return (
      <div className="rounded-xl border border-dashed border-white/10 p-5 text-xs text-white/35">
        Sin patrones repetidos. Buena señal.
      </div>
    );
  }

  const max = Math.max(...patterns.map((p) => p.count), 1);

  return (
    <ul className="space-y-2">
      {patterns.map((pattern) => {
        const href = `/matches/${pattern.match_ids[0]}`;
        return (
          <li key={pattern.rule_id}>
            <Link
              href={href}
              className="group block rounded-xl border border-white/5 bg-white/[0.015] p-3 transition hover:border-white/10 hover:bg-white/[0.035]"
            >
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0">
                  <div className="flex items-center gap-2">
                    <span
                      className={clsx(
                        "h-1.5 w-1.5 shrink-0 rounded-full",
                        pattern.severity >= 4 ? "bg-brand-500" : "bg-amber-400",
                      )}
                    />
                    <p className="truncate text-xs font-medium text-white/85">
                      {pattern.title}
                    </p>
                  </div>
                  <p className="mt-1 pl-3.5 text-[10px] uppercase tracking-[0.12em] text-white/30">
                    {pattern.category}
                  </p>
                </div>
                <div className="flex shrink-0 items-center gap-2">
                  <span className="num text-[11px] text-white/45">
                    {pattern.count}×
                  </span>
                  <ArrowUpRight
                    size={13}
                    className="text-white/20 transition group-hover:text-white/60"
                  />
                </div>
              </div>
              <div className="mt-2.5 ml-3.5 h-1 overflow-hidden rounded-full bg-white/[0.05]">
                <div
                  className={clsx(
                    "h-full rounded-full",
                    pattern.severity >= 4 ? "bg-brand-500/70" : "bg-amber-400/60",
                  )}
                  style={{ width: `${Math.max(12, (pattern.count / max) * 100)}%` }}
                />
              </div>
            </Link>
          </li>
        );
      })}
    </ul>
  );
}
