import { Minus, Shield, Swords } from "lucide-react";
import type { Round } from "@/lib/types";
import { clsx } from "./clsx";

function RoundPill({ round }: { round: Round }) {
  const isWin = round.won;
  const side = round.side;
  const SideIcon = side === "attack" ? Swords : side === "defense" ? Shield : Minus;
  const buyLabel =
    round.buy_type === "full"
      ? "compra completa"
      : round.buy_type === "force"
        ? "force"
        : round.buy_type === "save"
          ? "save"
          : null;
  const title = [
    `Ronda ${round.number}`,
    side === "attack" ? "Ataque" : side === "defense" ? "Defensa" : "Lado desconocido",
    isWin ? "Ganada" : "Perdida",
    `${round.kills}K / ${round.deaths}D / ${round.assists}A`,
    round.damage > 0 ? `${round.damage} daño` : null,
    round.weapon ?? "sin arma",
    round.abilities_used !== null ? `${round.abilities_used} habilidades` : null,
    round.first_blood ? "Primer blood" : null,
    round.first_death ? "Primera muerte" : null,
    round.traded_death ? "Tradeada" : null,
    buyLabel,
  ]
    .filter(Boolean)
    .join(" · ");

  return (
    <div
      title={title}
      className={clsx(
        "relative flex w-[46px] shrink-0 cursor-default flex-col items-center gap-1 rounded-lg border py-1.5 transition hover:-translate-y-0.5",
        isWin
          ? "border-mint-500/25 bg-mint-500/[0.07]"
          : "border-brand-500/20 bg-brand-500/[0.06]",
      )}
    >
      {(round.first_blood || round.first_death) && (
        <span
          className={clsx(
            "absolute right-1 top-1 h-1 w-1 rounded-full",
            round.first_death ? "bg-brand-500" : "bg-mint-400",
          )}
        />
      )}
      <span className="num text-[10px] font-medium text-white/55">{round.number}</span>
      <SideIcon
        size={11}
        className={isWin ? "text-mint-400/80" : "text-brand-400/80"}
      />
      <span className="num text-[8px] leading-none text-white/30">
        {round.kills}/{round.deaths}
      </span>
    </div>
  );
}

export function RoundTimeline({ rounds }: { rounds: Round[] }) {
  const first = rounds.slice(0, 12);
  const second = rounds.slice(12);
  const firstWins = first.filter((r) => r.won).length;
  const secondWins = second.filter((r) => r.won).length;

  return (
    <section className="panel p-5">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <h2 className="text-sm font-semibold tracking-tight">Timeline de rondas</h2>
          <p className="mt-0.5 text-[11px] text-white/35">
            Pasa el ratón por una ronda para ver el detalle.
          </p>
        </div>
        <div className="flex items-center gap-3 text-[10px] text-white/35">
          <span className="flex items-center gap-1.5">
            <span className="h-2 w-2 rounded-full bg-mint-400" /> Ganada
          </span>
          <span className="flex items-center gap-1.5">
            <span className="h-2 w-2 rounded-full bg-brand-500" /> Perdida
          </span>
          <span className="flex items-center gap-1.5">
            <span className="h-1.5 w-1.5 rounded-full bg-mint-400/70" /> Primer blood
          </span>
        </div>
      </div>

      <div className="mt-4 space-y-4">
        <div>
          <div className="mb-2 flex items-center justify-between">
            <p className="label-xs">Primera mitad</p>
            <p className="num text-[10px] text-white/30">{firstWins} ganadas</p>
          </div>
          <div className="flex gap-1.5 overflow-x-auto pb-1">
            {first.map((round) => (
              <RoundPill key={round.number} round={round} />
            ))}
          </div>
        </div>

        <div>
          <div className="mb-2 flex items-center justify-between">
            <p className="label-xs">Segunda mitad</p>
            <p className="num text-[10px] text-white/30">{secondWins} ganadas</p>
          </div>
          <div className="flex gap-1.5 overflow-x-auto pb-1">
            {second.map((round) => (
              <RoundPill key={round.number} round={round} />
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
