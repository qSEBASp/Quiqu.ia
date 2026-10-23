import type { TrendPoint } from "@/lib/types";
import { fmtDay } from "@/lib/format";

export function TrendChart({ points }: { points: TrendPoint[] }) {
  if (points.length === 0) {
    return (
      <div className="grid h-[200px] place-items-center text-xs text-white/30">
        Sin datos todavía
      </div>
    );
  }

  const width = 720;
  const height = 200;
  const padX = 18;
  const padTop = 18;
  const padBottom = 30;
  const values = points.map((p) => p.acs);
  const rawMin = Math.min(...values);
  const rawMax = Math.max(...values);
  const min = Math.max(0, Math.floor((rawMin - 30) / 20) * 20);
  const max = Math.max(min + 60, Math.ceil((rawMax + 30) / 20) * 20);
  const span = max - min;

  const x = (index: number) =>
    padX + (index * (width - padX * 2)) / Math.max(1, points.length - 1);
  const y = (value: number) =>
    padTop + (1 - (value - min) / span) * (height - padTop - padBottom);

  const line = points.map((p, i) => `${i === 0 ? "M" : "L"} ${x(i)} ${y(p.acs)}`).join(" ");
  const area = `${line} L ${x(points.length - 1)} ${height - padBottom} L ${x(0)} ${height - padBottom} Z`;
  const gridValues = [min, min + span / 2, max];

  return (
    <div className="w-full">
      <svg
        viewBox={`0 0 ${width} ${height}`}
        className="h-[200px] w-full"
        role="img"
        aria-label="Evolución de ACS por partida"
      >
        <defs>
          <linearGradient id="trend-area" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#ff4655" stopOpacity="0.22" />
            <stop offset="100%" stopColor="#ff4655" stopOpacity="0" />
          </linearGradient>
        </defs>

        {gridValues.map((value) => (
          <g key={value}>
            <line
              x1={padX}
              x2={width - padX}
              y1={y(value)}
              y2={y(value)}
              stroke="rgba(255,255,255,0.055)"
              strokeDasharray="3 6"
            />
            <text
              x={padX}
              y={y(value) - 6}
              fill="rgba(255,255,255,0.28)"
              fontSize="10"
              fontFamily="var(--font-mono)"
            >
              {Math.round(value)}
            </text>
          </g>
        ))}

        <path d={area} fill="url(#trend-area)" />
        <path
          d={line}
          fill="none"
          stroke="#ff6b77"
          strokeWidth="2"
          strokeLinejoin="round"
          strokeLinecap="round"
        />

        {points.map((point, index) => (
          <g key={point.id}>
            <circle
              cx={x(index)}
              cy={y(point.acs)}
              r={4}
              fill={point.result === "win" ? "#53e6b5" : "#ff4655"}
              stroke="#0b0d12"
              strokeWidth="2"
            >
              <title>
                {`${point.map} · ${point.acs} ACS · ${point.result === "win" ? "Victoria" : "Derrota"}`}
              </title>
            </circle>
          </g>
        ))}

        {points.map((point, index) => {
          const show =
            index === 0 ||
            index === points.length - 1 ||
            index === Math.floor(points.length / 2);
          if (!show) return null;
          return (
            <text
              key={`label-${point.id}`}
              x={x(index)}
              y={height - 8}
              textAnchor={
                index === 0 ? "start" : index === points.length - 1 ? "end" : "middle"
              }
              fill="rgba(255,255,255,0.28)"
              fontSize="10"
            >
              {fmtDay(point.date)}
            </text>
          );
        })}
      </svg>
    </div>
  );
}
