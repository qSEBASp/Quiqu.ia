from dataclasses import dataclass, field
from typing import Any

from ..providers.base import MatchData


@dataclass
class Finding:
    rule_id: str
    category: str
    severity: int
    title: str
    detail: str
    recommendation: str
    metric: float | None = None
    threshold: float | None = None
    evidence: dict[str, Any] = field(default_factory=dict)


def _round_list(rounds: list) -> list[int]:
    return [r.number for r in rounds]


def evaluate(match: MatchData, metrics: dict) -> list[Finding]:
    rounds = match.rounds
    total = len(rounds)
    if total == 0:
        return []

    findings: list[Finding] = []
    deaths = match.overall.deaths or sum(r.deaths for r in rounds)

    fd_rounds = [r for r in rounds if r.first_death]
    fd_rate = metrics["fd_rate"]
    if len(fd_rounds) >= 4 and fd_rate >= 20:
        findings.append(
            Finding(
                rule_id="first_death_rate",
                category="Duelos",
                severity=4,
                title="Regalas demasiados primeros contactos",
                detail=(
                    f"Moriste en el primer contacto en {len(fd_rounds)} de {total} rondas "
                    f"({fd_rate:.0f}%). Cada primer contacto perdido deja a tu equipo en 4v5 "
                    "y suele costar la ronda."
                ),
                recommendation=(
                    "Juega 3 partidas sin ser el primero en asomarte: espera a que un compañero "
                    "abra el duelo o usa una habilidad para ganar información antes de entrar."
                ),
                metric=fd_rate,
                threshold=20,
                evidence={"rounds": _round_list(fd_rounds)},
            )
        )

    untraded = [r for r in rounds if r.deaths > 0 and not r.traded_death]
    trade_rate = metrics["trade_rate"]
    if deaths >= 8 and trade_rate < 35:
        findings.append(
            Finding(
                rule_id="untraded_deaths",
                category="Duelos",
                severity=3,
                title="Tus muertes no se están tradeando",
                detail=(
                    f"Solo el {trade_rate:.0f}% de tus muertes fueron tradeadas. "
                    f"{len(untraded)} muertes quedaron sin respuesta de un compañero."
                ),
                recommendation=(
                    "Acuerda con tu dúo una regla simple: si uno entra, el otro está a menos de "
                    "5 segundos para tradearte. Evita entrar solo sin cobertura."
                ),
                metric=trade_rate,
                threshold=35,
                evidence={"rounds": _round_list(untraded)},
            )
        )

    known_attack = [
        r
        for r in rounds
        if r.side == "attack" and r.abilities_used is not None and r.loadout_value >= 1500
    ]
    zero_util = [r for r in known_attack if r.abilities_used == 0]
    if len(known_attack) >= 4 and len(zero_util) >= 3:
        findings.append(
            Finding(
                rule_id="attack_no_utility",
                category="Utilidad",
                severity=4,
                title="Estás entrando sin utilidad",
                detail=(
                    f"En {len(zero_util)} de {len(known_attack)} rondas de ataque con compra "
                    "usaste cero habilidades. Entrar sin humo, flash o info regala los duelos."
                ),
                recommendation=(
                    "Antes de cada ataque define qué habilidad abre la entrada y úsala en los "
                    "primeros 20 segundos. Si no la usas, no la compres."
                ),
                metric=float(len(zero_util)),
                threshold=3,
                evidence={"rounds": _round_list(zero_util)},
            )
        )

    if metrics["force_buys"] >= 3:
        findings.append(
            Finding(
                rule_id="force_buy_after_loss",
                category="Economía",
                severity=3,
                title="Fuerzas compras tras perder la ronda",
                detail=(
                    f"Forzaste la compra {metrics['force_buys']} veces después de una ronda "
                    "perdida. Eso rompe la economía para las rondas siguientes y regala ventaja "
                    "de armas al rival."
                ),
                recommendation=(
                    "Define dos reglas de compra por partida: full buy desde 3.900 créditos y "
                    "save por debajo de 2.000. En el save, compra solo pistola y armadura ligera."
                ),
                metric=float(metrics["force_buys"]),
                threshold=3,
                evidence={
                    "rounds": _round_list(
                        [r for r in rounds if r.buy_type == "force"]
                    )
                },
            )
        )

    if metrics["no_armor_buys"] >= 2:
        armor_rounds = [
            r for r in rounds if not r.has_armor and r.loadout_value >= 2000
        ]
        findings.append(
            Finding(
                rule_id="buy_without_armor",
                category="Economía",
                severity=2,
                title="Compras arma sin armadura",
                detail=(
                    f"En {len(armor_rounds)} rondas compraste un arma cara sin armadura. "
                    "Un disparo a la cabeza o dos al cuerpo te dejan fuera del duelo."
                ),
                recommendation=(
                    "Si vas a comprar rifle, compra siempre armadura completa. Si no llega, "
                    "baja a Spectre + armadura antes que Vandal sin chaleco."
                ),
                metric=float(len(armor_rounds)),
                threshold=2,
                evidence={"rounds": _round_list(armor_rounds)},
            )
        )

    if total >= 8 and metrics["kast"] < 65:
        findings.append(
            Finding(
                rule_id="low_kast",
                category="Impacto",
                severity=3,
                title="Poco impacto por ronda",
                detail=(
                    f"Tu KAST es {metrics['kast']:.0f}% (referencia sana: 70%+). En demasiadas "
                    "rondas no aportas kill, asistencia, supervivencia ni trade."
                ),
                recommendation=(
                    "Prioriza sobrevivir y tradeear antes que buscar kills aisladas. Revisa tus "
                    "3 muertes más tempranas y evita repetir esa posición."
                ),
                metric=metrics["kast"],
                threshold=65,
            )
        )

    if total >= 8 and metrics["hs_pct"] < 20:
        findings.append(
            Finding(
                rule_id="low_headshot_pct",
                category="Aim",
                severity=2,
                title="Poco porcentaje de headshots",
                detail=(
                    f"Tu HS% es {metrics['hs_pct']:.1f}%. Estás ganando duelos por volumen de "
                    "daño y no por precisión."
                ),
                recommendation=(
                    "10 minutos de Aim Lab o rango de tiro antes de jugar: fija la mira a altura "
                    "de cabeza y haz flicks cortos, no barridos largos."
                ),
                metric=metrics["hs_pct"],
                threshold=20,
            )
        )

    if total >= 8 and metrics["adr"] < 120:
        findings.append(
            Finding(
                rule_id="low_adr",
                category="Impacto",
                severity=3,
                title="Daño por ronda bajo",
                detail=(
                    f"Tu ADR es {metrics['adr']:.0f}. Por debajo de 120 suele indicar que llegas "
                    "tarde a los duelos o que mueres sin intercambiar daño."
                ),
                recommendation=(
                    "Juega más cerca de tu equipo y participa en los duelos con daño previo: "
                    "una flash o un disparo de cobertura antes de entrar."
                ),
                metric=metrics["adr"],
                threshold=120,
            )
        )

    if metrics["attack_rounds"] >= 5 and metrics["attack_winrate"] < 40:
        findings.append(
            Finding(
                rule_id="weak_attack_side",
                category="Lados",
                severity=3,
                title="Tu ataque es el lado débil",
                detail=(
                    f"Ganas el {metrics['attack_winrate']:.0f}% de tus rondas de ataque "
                    f"({metrics['attack_rounds']} rondas). El problema no es el aim, es la "
                    "ejecución de entrada."
                ),
                recommendation=(
                    "Elige un sitio por ronda, usa utilidad para cortar la retaguardia y entra "
                    "todos juntos. Prohibido entrar de uno en uno."
                ),
                metric=metrics["attack_winrate"],
                threshold=40,
            )
        )

    if metrics["defense_rounds"] >= 5 and metrics["defense_winrate"] < 40:
        findings.append(
            Finding(
                rule_id="weak_defense_side",
                category="Lados",
                severity=3,
                title="Tu defensa es el lado débil",
                detail=(
                    f"Ganas el {metrics['defense_winrate']:.0f}% de tus rondas de defensa "
                    f"({metrics['defense_rounds']} rondas). Estás regalando el mapa en el lado "
                    "defensivo."
                ),
                recommendation=(
                    "No repitas la misma posición dos rondas seguidas. Juega retrasado con "
                    "compañero y pide info antes de rotar."
                ),
                metric=metrics["defense_winrate"],
                threshold=40,
            )
        )

    if total >= 10 and metrics["kpr"] < 0.6 and metrics["fb_rate"] < 12:
        findings.append(
            Finding(
                rule_id="low_individual_impact",
                category="Impacto",
                severity=3,
                title="Impacto individual bajo",
                detail=(
                    f"Promedias {metrics['kpr']:.2f} kills por ronda y solo abres el marcador "
                    f"en el {metrics['fb_rate']:.0f}% de las rondas. Estás jugando demasiado "
                    "pasivo."
                ),
                recommendation=(
                    "En defensa, toma una posición agresiva con salida segura y busca un primer "
                    "contacto por ronda. En ataque, acompaña la entrada con daño."
                ),
                metric=metrics["kpr"],
                threshold=0.6,
            )
        )

    findings.sort(key=lambda f: (f.severity, f.metric or 0), reverse=True)
    return findings
