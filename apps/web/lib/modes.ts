export interface GameMode {
  id: string;
  label: string;
  aliases: string[];
  /** El analizador solo guarda modos con rondas. */
  analyzed: boolean;
  hint: string;
}

export const GAME_MODES: GameMode[] = [
  {
    id: "competitive",
    label: "Competitivo",
    aliases: ["competitive", "competitivo", "competitiva", "ranked", "rank"],
    analyzed: true,
    hint: "Ranked con puntos de rango.",
  },
  {
    id: "unrated",
    label: "Unrated",
    aliases: ["unrated", "unranked", "sin rank", "normal", "no competitivo"],
    analyzed: true,
    hint: "Partidas normales sin rango.",
  },
  {
    id: "swiftplay",
    label: "Swiftplay",
    aliases: ["swiftplay", "swift play", "swift"],
    analyzed: true,
    hint: "Partidas cortas, primera a 5 rondas.",
  },
  {
    id: "spike_rush",
    label: "Spike Rush",
    aliases: ["spike rush", "spikerush", "spike", "fiebre de la spike"],
    analyzed: true,
    hint: "Rondas rápidas con armas aleatorias.",
  },
  {
    id: "premier",
    label: "Premier",
    aliases: ["premier", "premier league"],
    analyzed: true,
    hint: "Liga por equipos dentro del juego.",
  },
  {
    id: "deathmatch",
    label: "Deathmatch",
    aliases: ["deathmatch", "death match", "dm"],
    analyzed: false,
    hint: "Sin rondas: no se analiza.",
  },
  {
    id: "team_deathmatch",
    label: "Team Deathmatch",
    aliases: ["team deathmatch", "team death match", "tdm", "deathmatch por equipos"],
    analyzed: false,
    hint: "Sin rondas: no se analiza.",
  },
  {
    id: "escalation",
    label: "Escalation",
    aliases: ["escalation", "escalada"],
    analyzed: false,
    hint: "Sin rondas: no se analiza.",
  },
  {
    id: "custom",
    label: "Custom",
    aliases: ["custom", "custom game", "personalizada", "partida personalizada"],
    analyzed: false,
    hint: "Personalizadas: no se analizan.",
  },
];

export const ANALYZED_MODES = GAME_MODES.filter((mode) => mode.analyzed);

function normalize(value: string): string {
  return value
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, " ")
    .trim();
}

const INDEX = new Map<string, GameMode>();
for (const mode of GAME_MODES) {
  INDEX.set(normalize(mode.id), mode);
  INDEX.set(normalize(mode.label), mode);
  for (const alias of mode.aliases) INDEX.set(normalize(alias), mode);
}

export function modeInfo(rawMode: string): { id: string; label: string } {
  const match = INDEX.get(normalize(rawMode));
  return match
    ? { id: match.id, label: match.label }
    : { id: normalize(rawMode) || "unknown", label: rawMode };
}
