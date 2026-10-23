const dateFmt = new Intl.DateTimeFormat("es-ES", {
  day: "2-digit",
  month: "short",
  hour: "2-digit",
  minute: "2-digit",
});

const dayFmt = new Intl.DateTimeFormat("es-ES", {
  day: "2-digit",
  month: "short",
});

export function fmtDate(value?: string | null): string {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "—";
  return dateFmt.format(date);
}

export function fmtDay(value?: string | null): string {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "—";
  return dayFmt.format(date);
}

export function pct(value: number, digits = 0): string {
  return `${value.toFixed(digits)}%`;
}

export function num(value: number, digits = 0): string {
  return value.toFixed(digits);
}

export function signed(value: number): string {
  return value > 0 ? `+${value}` : `${value}`;
}

export function kda(kills: number, deaths: number, assists: number): string {
  return `${kills}/${deaths}/${assists}`;
}

export function initials(name: string): string {
  const clean = name.trim();
  if (!clean) return "?";
  return clean.slice(0, 2).toUpperCase();
}

export function resultLabel(result: string): string {
  if (result === "win") return "Victoria";
  if (result === "loss") return "Derrota";
  return "Empate";
}

export function sideLabel(side: string): string {
  if (side === "attack") return "Ataque";
  if (side === "defense") return "Defensa";
  return "—";
}
