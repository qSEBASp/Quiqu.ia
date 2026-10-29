from dataclasses import dataclass

from .messages import pick_index

MIN_ROUNDS = 8


@dataclass
class Strength:
    rule_id: str
    category: str
    title: str
    summary: str
    detail: str
    tier: int
    metric: float | None = None


# (titulo, resumen, detalle) por variante. Se elige de forma determinista con
# el id de la partida, igual que las reglas, para no repetir siempre lo mismo.
STRENGTH_COPY: dict[str, tuple[tuple[str, str, str], ...]] = {
    "high_impact": (
        (
            "Impacto alto y constante",
            "Sostienes el intercambio con daño real en las rondas que juegas.",
            "Promedias {acs:.0f} ACS y {adr:.0f} ADR. Entras a los duelos con daño real "
            "y sostienes el intercambio en casi todas las rondas.",
        ),
        (
            "Daño que pesa en cada ronda",
            "Tu daño por ronda está por encima de la media y se nota en el marcador.",
            "{acs:.0f} ACS y {adr:.0f} ADR. No dependes de una ronda buena: el impacto "
            "aparece de forma repetida.",
        ),
    ),
    "first_contact_edge": (
        (
            "Ganas los primeros contactos",
            "Ganas más duelos de apertura de los que pierdes y das ventaja a tu equipo.",
            "Abres el marcador en el {fb:.0f}% de las rondas y solo mueres primero en el "
            "{fd:.0f}%. Tu equipo entra con ventaja numérica.",
        ),
        (
            "Tu equipo entra primero gracias a ti",
            "La apertura de ronda es tuya más veces de las que la pierdes.",
            "{fb:.0f}% de primeros contactos ganados frente a {fd:.0f}% de primeras "
            "muertes. Sales ganando el pulso inicial.",
        ),
    ),
    "sharp_aim": (
        (
            "Precisión de cabeza",
            "Ganas duelos por colocación de mira, no por volumen de disparos.",
            "Tu HS% es {hs:.1f}%. Ganas duelos por colocación de mira y no por volumen "
            "de disparos.",
        ),
        (
            "La mira está donde debe",
            "Disparas a la cabeza más que la media y eso acorta los duelos.",
            "HS% del {hs:.1f}%. Necesitas menos balas para cerrar cada duelo.",
        ),
    ),
    "team_trades": (
        (
            "Tus muertes se cobran",
            "Juegas cerca de tu equipo y tus muertes casi nunca quedan sin cobrar.",
            "El {trade:.0f}% de tus muertes se tradean. Juegas cerca de tu equipo y no "
            "regalas ventaja numérica.",
        ),
        (
            "Nunca mueres solo",
            "Cuando caes, un compañero suele cobrar el duelo.",
            "Trade rate del {trade:.0f}%. Tu forma de entrar permite que el equipo "
            "convierta tus muertes en ventaja.",
        ),
    ),
    "clean_economy": (
        (
            "Economía disciplinada",
            "Administras los créditos sin forzar rondas rotas.",
            "Compras sin forzar rondas rotas y llegas a los full buys con créditos. Tu "
            "economía no regala ventaja de armas.",
        ),
        (
            "Los créditos no se tiran",
            "Tus compras sostienen el ritmo de la partida.",
            "Econ score del {econ:.0f}. Evitas fuerzas innecesarias y llegas a las rondas "
            "clave con dinero.",
        ),
    ),
    "strong_attack": (
        (
            "Ataque sólido",
            "La ejecución de entrada funciona: ganas más de la mitad de tus ataques.",
            "Ganas el {rate:.0f}% de tus rondas de ataque ({rounds} rondas). La ejecución "
            "de entrada está funcionando.",
        ),
        (
            "Tus entradas se convierten",
            "El ataque es un lado rentable para ti.",
            "{rate:.0f}% de winrate atacando en {rounds} rondas. Estás encontrando la "
            "forma de abrir y cerrar los sitios.",
        ),
    ),
    "strong_defense": (
        (
            "Defensa sólida",
            "Lees bien los tiempos del rival y defiendes con ventaja.",
            "Ganas el {rate:.0f}% de tus rondas de defensa ({rounds} rondas). Estás "
            "leyendo bien los tiempos del rival.",
        ),
        (
            "Aguantas el mapa en defensa",
            "Tus posiciones defensivas están dando resultado.",
            "{rate:.0f}% de winrate defendiendo en {rounds} rondas. El rival no encuentra "
            "huecos fáciles.",
        ),
    ),
    "high_kast": (
        (
            "Presente en casi todas las rondas",
            "Rara vez haces una ronda en blanco: aportas kill, asistencia, trade o "
            "supervivencia.",
            "Tu KAST es {kast:.0f}%. Aportas en casi todas las rondas, aunque no siempre "
            "sea con kills.",
        ),
        (
            "Nunca desapareces de la ronda",
            "Tu aportación no depende solo de matar.",
            "KAST del {kast:.0f}%. Cubres, asistes y sobrevives lo suficiente para estar "
            "en la jugada.",
        ),
    ),
    "low_deaths": (
        (
            "Mueres poco",
            "Cuidas tu vida sin dejar de participar en los duelos.",
            "Promedias {dpr:.2f} muertes por ronda. Cuidas tu vida sin dejar de participar "
            "en los duelos.",
        ),
        (
            "La vida te dura más",
            "Sobrevives más que la media sin esconderte de la pelea.",
            "{dpr:.2f} muertes por ronda. Sigues entrando a los duelos, pero sales más "
            "veces de ellos.",
        ),
    ),
}


def _copy(seed: str, rule_id: str, context: dict) -> tuple[str, str, str]:
    options = STRENGTH_COPY[rule_id]
    title, summary, detail = options[
        pick_index(seed or "sin-id", f"strength:{rule_id}", len(options))
    ]
    return title.format(**context), summary.format(**context), detail.format(**context)


def evaluate_strengths(metrics: dict, seed: str = "") -> list[Strength]:
    """Puntos fuertes medibles de una partida.

    Se calculan al vuelo desde las metricas guardadas, asi que tambien
    funcionan con partidas ya persistidas (no toca el esquema). El ``seed``
    suele ser el id de la partida y solo cambia la redaccion.
    """
    rounds = metrics.get("rounds", 0)
    if rounds < MIN_ROUNDS:
        return []

    acs = metrics.get("acs", 0.0)
    adr = metrics.get("adr", 0.0)
    hs_pct = metrics.get("hs_pct", 0.0)
    kast = metrics.get("kast", 0.0)
    dpr = metrics.get("dpr", 0.0)
    trade_rate = metrics.get("trade_rate", 0.0)
    fb_rate = metrics.get("fb_rate", 0.0)
    fd_rate = metrics.get("fd_rate", 0.0)
    econ_score = metrics.get("econ_score", 0.0)
    attack_rounds = metrics.get("attack_rounds", 0)
    defense_rounds = metrics.get("defense_rounds", 0)
    attack_winrate = metrics.get("attack_winrate", 0.0)
    defense_winrate = metrics.get("defense_winrate", 0.0)

    strengths: list[Strength] = []

    if acs >= 230 and adr >= 150:
        title, summary, detail = _copy(
            seed,
            "high_impact",
            {"acs": acs, "adr": adr},
        )
        strengths.append(
            Strength(
                rule_id="high_impact",
                category="Impacto",
                tier=3,
                title=title,
                summary=summary,
                detail=detail,
                metric=acs,
            )
        )

    if fb_rate >= 20 and fd_rate <= 12:
        title, summary, detail = _copy(
            seed,
            "first_contact_edge",
            {"fb": fb_rate, "fd": fd_rate},
        )
        strengths.append(
            Strength(
                rule_id="first_contact_edge",
                category="Duelos",
                tier=3,
                title=title,
                summary=summary,
                detail=detail,
                metric=fb_rate,
            )
        )

    if hs_pct >= 25:
        title, summary, detail = _copy(seed, "sharp_aim", {"hs": hs_pct})
        strengths.append(
            Strength(
                rule_id="sharp_aim",
                category="Aim",
                tier=2,
                title=title,
                summary=summary,
                detail=detail,
                metric=hs_pct,
            )
        )

    if trade_rate >= 45:
        title, summary, detail = _copy(
            seed, "team_trades", {"trade": trade_rate}
        )
        strengths.append(
            Strength(
                rule_id="team_trades",
                category="Duelos",
                tier=2,
                title=title,
                summary=summary,
                detail=detail,
                metric=trade_rate,
            )
        )

    if econ_score >= 90:
        title, summary, detail = _copy(
            seed, "clean_economy", {"econ": econ_score}
        )
        strengths.append(
            Strength(
                rule_id="clean_economy",
                category="Economía",
                tier=2,
                title=title,
                summary=summary,
                detail=detail,
                metric=econ_score,
            )
        )

    if attack_rounds >= 5 and attack_winrate >= 60:
        title, summary, detail = _copy(
            seed,
            "strong_attack",
            {"rate": attack_winrate, "rounds": attack_rounds},
        )
        strengths.append(
            Strength(
                rule_id="strong_attack",
                category="Lados",
                tier=2,
                title=title,
                summary=summary,
                detail=detail,
                metric=attack_winrate,
            )
        )

    if defense_rounds >= 5 and defense_winrate >= 60:
        title, summary, detail = _copy(
            seed,
            "strong_defense",
            {"rate": defense_winrate, "rounds": defense_rounds},
        )
        strengths.append(
            Strength(
                rule_id="strong_defense",
                category="Lados",
                tier=2,
                title=title,
                summary=summary,
                detail=detail,
                metric=defense_winrate,
            )
        )

    if kast >= 75:
        title, summary, detail = _copy(seed, "high_kast", {"kast": kast})
        strengths.append(
            Strength(
                rule_id="high_kast",
                category="Impacto",
                tier=2,
                title=title,
                summary=summary,
                detail=detail,
                metric=kast,
            )
        )

    if dpr <= 0.55:
        title, summary, detail = _copy(seed, "low_deaths", {"dpr": dpr})
        strengths.append(
            Strength(
                rule_id="low_deaths",
                category="Duelos",
                tier=1,
                title=title,
                summary=summary,
                detail=detail,
                metric=dpr,
            )
        )

    strengths.sort(key=lambda s: (s.tier, s.metric or 0), reverse=True)
    return strengths[:3]
