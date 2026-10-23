import type { ReactNode } from "react";
import { clsx } from "./clsx";

const tones = {
  neutral: "text-white",
  mint: "text-mint-400",
  brand: "text-brand-400",
  amber: "text-amber-400",
  sky: "text-sky-400",
};

export function StatCard({
  label,
  value,
  suffix,
  description,
  tone = "neutral",
  badge,
}: {
  label: string;
  value: string | number;
  suffix?: string;
  description?: string;
  tone?: keyof typeof tones;
  badge?: ReactNode;
}) {
  return (
    <div className="panel relative overflow-hidden p-4 sm:p-5">
      <div className="flex items-start justify-between gap-3">
        <p className="label-xs">{label}</p>
        {badge}
      </div>
      <div className="mt-3 flex items-baseline gap-1.5">
        <span
          className={clsx(
            "num text-[28px] font-semibold leading-none tracking-[-0.02em] sm:text-[32px]",
            tones[tone],
          )}
        >
          {value}
        </span>
        {suffix && (
          <span className="text-xs font-medium text-white/35">{suffix}</span>
        )}
      </div>
      {description && (
        <p className="mt-2 text-[11px] leading-relaxed text-white/35">{description}</p>
      )}
    </div>
  );
}
