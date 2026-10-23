import re
import unicodedata

# Ids canonicos compartidos con apps/web/lib/modes.ts. El backend los usa para
# filtrar por modo sin depender de si Henrik devuelve el nombre en ingles o la
# demo en espanol.
MODE_ALIASES: dict[str, set[str]] = {
    "competitive": {"competitive", "competitivo", "competitiva", "ranked", "rank"},
    "unrated": {"unrated", "unranked", "sin rank", "normal", "no competitivo"},
    "swiftplay": {"swiftplay", "swift play", "swift"},
    "spike_rush": {"spike rush", "spikerush", "spike", "fiebre de la spike"},
    "premier": {"premier", "premier league"},
    "deathmatch": {"deathmatch", "death match", "dm"},
    "team_deathmatch": {"team deathmatch", "team death match", "tdm"},
    "escalation": {"escalation", "escalada"},
    "custom": {"custom", "custom game", "personalizada", "partida personalizada"},
}

ANALYZED_MODES = [
    "competitive",
    "unrated",
    "swiftplay",
    "spike_rush",
    "premier",
]

_LABELS = {
    "competitive": "Competitivo",
    "unrated": "Unrated",
    "swiftplay": "Swiftplay",
    "spike_rush": "Spike Rush",
    "premier": "Premier",
    "deathmatch": "Deathmatch",
    "team_deathmatch": "Team Deathmatch",
    "escalation": "Escalation",
    "custom": "Custom",
}

_INDEX = {
    alias: mode_id for mode_id, aliases in MODE_ALIASES.items() for alias in aliases
}


def _slug(value: str) -> str:
    normalized = unicodedata.normalize("NFD", value or "")
    normalized = "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")
    return re.sub(r"[^a-z0-9]+", " ", normalized.lower()).strip()


def normalize_mode(value: str | None) -> str:
    """Devuelve el id canonico del modo o un slug estable si es desconocido."""
    slug = _slug(value or "")
    return _INDEX.get(slug, slug or "unknown")


def mode_label(value: str | None) -> str:
    mode_id = normalize_mode(value)
    return _LABELS.get(mode_id, (value or "").strip() or "Desconocido")


def mode_matches(value: str | None, mode_id: str) -> bool:
    return normalize_mode(value) == mode_id
