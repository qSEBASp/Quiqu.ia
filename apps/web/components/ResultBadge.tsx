import { clsx } from "./clsx";

export function ResultBadge({
  result,
  score,
  size = "md",
}: {
  result: string;
  score?: string;
  size?: "sm" | "md";
}) {
  const isWin = result === "win";
  const isDraw = result === "draw";
  return (
    <span
      className={clsx(
        "inline-flex items-center gap-2 rounded-lg border font-semibold",
        size === "sm" ? "px-2 py-0.5 text-[11px]" : "px-2.5 py-1 text-xs",
        isWin
          ? "border-mint-500/25 bg-mint-500/10 text-mint-400"
          : isDraw
            ? "border-white/10 bg-white/5 text-white/60"
            : "border-brand-500/25 bg-brand-500/10 text-brand-400",
      )}
    >
      {isWin ? "Victoria" : isDraw ? "Empate" : "Derrota"}
      {score && <span className="num text-[0.92em] opacity-80">{score}</span>}
    </span>
  );
}
