from dataclasses import dataclass

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


def evaluate_strengths(metrics: dict) -> list[Strength]:
    """Puntos fuertes medibles de una partida.

    Se calculan al vuelo desde las metricas guardadas, asi que tambien
    funcionan con partidas ya persistidas (no toca el esquema).
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
        strengths.append(
            Strength(
                rule_id="high_impact",
                category="Impacto",
                tier=3,
                title="Impacto alto y constante",
                summary="Sostienes el intercambio con daño real en las rondas que juegas.",
                detail=(
                    f"Promedias {acs:.0f} ACS y {adr:.0f} ADR. Entras a los duelos con daño "
                    "real y sostienes el intercambio en casi todas las rondas."
                ),
                metric=acs,
            )
        )

    if fb_rate >= 20 and fd_rate <= 12:
        strengths.append(
            Strength(
                rule_id="first_contact_edge",
                category="Duelos",
                tier=3,
                title="Ganas los primeros contactos",
                summary="Ganas más duelos de apertura de los que pierdes y das ventaja a tu equipo.",
                detail=(
                    f"Abres el marcador en el {fb_rate:.0f}% de las rondas y solo mueres "
                    f"primero en el {fd_rate:.0f}%. Tu equipo entra con ventaja numerica."
                ),
                metric=fb_rate,
            )
        )

    if hs_pct >= 25:
        strengths.append(
            Strength(
                rule_id="sharp_aim",
                category="Aim",
                tier=2,
                title="Precisión de cabeza",
                summary="Ganas duelos por colocación de mira, no por volumen de disparos.",
                detail=(
                    f"Tu HS% es {hs_pct:.1f}%. Ganas duelos por colocación de mira y no por "
                    "volumen de disparos."
                ),
                metric=hs_pct,
            )
        )

    if trade_rate >= 45:
        strengths.append(
            Strength(
                rule_id="team_trades",
                category="Duelos",
                tier=2,
                title="Tus muertes se cobran",
                summary="Juegas cerca de tu equipo y tus muertes casi nunca quedan sin cobrar.",
                detail=(
                    f"El {trade_rate:.0f}% de tus muertes se tradean. Juegas cerca de tu "
                    "equipo y no regalas ventaja numerica."
                ),
                metric=trade_rate,
            )
        )

    if econ_score >= 90:
        strengths.append(
            Strength(
                rule_id="clean_economy",
                category="Economía",
                tier=2,
                title="Economía disciplinada",
                summary="Administras los créditos sin forzar rondas rotas.",
                detail=(
                    "Compras sin forzar rondas rotas y llegas a los full buy con créditos. "
                    "Tu economía no regala ventaja de armas."
                ),
                metric=econ_score,
            )
        )

    if attack_rounds >= 5 and attack_winrate >= 60:
        strengths.append(
            Strength(
                rule_id="strong_attack",
                category="Lados",
                tier=2,
                title="Ataque sólido",
                summary="La ejecución de entrada funciona: ganas más de la mitad de tus ataques.",
                detail=(
                    f"Ganas el {attack_winrate:.0f}% de tus rondas de ataque "
                    f"({attack_rounds} rondas). La ejecución de entrada está funcionando."
                ),
                metric=attack_winrate,
            )
        )

    if defense_rounds >= 5 and defense_winrate >= 60:
        strengths.append(
            Strength(
                rule_id="strong_defense",
                category="Lados",
                tier=2,
                title="Defensa sólida",
                summary="Lees bien los tiempos del rival y defiendes con ventaja.",
                detail=(
                    f"Ganas el {defense_winrate:.0f}% de tus rondas de defensa "
                    f"({defense_rounds} rondas). Estás leyendo bien los tiempos del rival."
                ),
                metric=defense_winrate,
            )
        )

    if kast >= 75:
        strengths.append(
            Strength(
                rule_id="high_kast",
                category="Impacto",
                tier=2,
                title="Presente en casi todas las rondas",
                summary="Rara vez haces una ronda en blanco: aportas kill, asistencia, trade o supervivencia.",
                detail=(
                    f"Tu KAST es {kast:.0f}%. Rara vez haces una ronda en blanco: aportas "
                    "kill, asistencia, trade o supervivencia."
                ),
                metric=kast,
            )
        )

    if dpr <= 0.55:
        strengths.append(
            Strength(
                rule_id="low_deaths",
                category="Duelos",
                tier=1,
                title="Mueres poco",
                summary="Cuidas tu vida sin dejar de participar en los duelos.",
                detail=(
                    f"Promedias {dpr:.2f} muertes por ronda. Cuidas tu vida sin dejar de "
                    "participar en los duelos."
                ),
                metric=dpr,
            )
        )

    strengths.sort(key=lambda s: (s.tier, s.metric or 0), reverse=True)
    return strengths[:3]
