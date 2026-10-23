import type { Metrics } from "@/lib/types";

export function MetricGrid({ metrics }: { metrics: Metrics }) {
  const items = [
    { label: "ACS", value: metrics.acs.toFixed(0), hint: "combate" },
    { label: "ADR", value: metrics.adr.toFixed(0), hint: "daño/ronda" },
    { label: "HS%", value: `${metrics.hs_pct.toFixed(0)}%`, hint: "precisión" },
    { label: "KAST", value: `${metrics.kast.toFixed(0)}%`, hint: "consistencia" },
    { label: "K/D", value: metrics.kd.toFixed(2), hint: "duelos" },
    { label: "Trades", value: `${metrics.trade_rate.toFixed(0)}%`, hint: "muertes cubiertas" },
    {
      label: "Economía",
      value: `${metrics.econ_score.toFixed(0)}`,
      hint: "disciplina",
    },
    {
      label: "Ataque",
      value: `${metrics.attack_winrate.toFixed(0)}%`,
      hint: `${metrics.attack_rounds} rondas`,
    },
  ];

  return (
    <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
      {items.map((item) => (
        <div
          key={item.label}
          className="rounded-xl border border-white/5 bg-white/[0.015] px-3 py-2.5"
        >
          <p className="text-[9px] uppercase tracking-[0.14em] text-white/30">
            {item.label}
          </p>
          <p className="num mt-1 text-lg font-semibold leading-none text-white/90">
            {item.value}
          </p>
          <p className="mt-1 text-[9px] text-white/25">{item.hint}</p>
        </div>
      ))}
    </div>
  );
}
