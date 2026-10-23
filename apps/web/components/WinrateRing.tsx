import { pct } from "@/lib/format";

export function WinrateRing({ winrate, wins, losses }: { winrate: number; wins: number; losses: number }) {
  const radius = 42;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference * (1 - Math.min(100, Math.max(0, winrate)) / 100);
  const color = winrate >= 50 ? "#53e6b5" : "#ff4655";

  return (
    <div className="relative grid h-[92px] w-[92px] place-items-center">
      <svg viewBox="0 0 100 100" className="h-full w-full -rotate-90">
        <circle
          cx="50"
          cy="50"
          r={radius}
          fill="none"
          stroke="rgba(255,255,255,0.06)"
          strokeWidth="8"
        />
        <circle
          cx="50"
          cy="50"
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth="8"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          style={{ transition: "stroke-dashoffset 600ms ease" }}
        />
      </svg>
      <div className="absolute inset-0 grid place-items-center">
        <div className="text-center">
          <div className="num text-lg font-semibold leading-none">{pct(winrate)}</div>
          <div className="mt-1 text-[9px] uppercase tracking-[0.14em] text-white/35">
            {wins}V · {losses}D
          </div>
        </div>
      </div>
    </div>
  );
}
