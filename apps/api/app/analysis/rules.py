from dataclasses import dataclass, field
from typing import Any

from ..providers.base import MatchData
from . import messages


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
    label: str = ""


def _round_list(rounds: list) -> list[int]:
    return [r.number for r in rounds]


def _build(
    match_id: str,
    rule_id: str,
    category: str,
    severity: int,
    context: dict[str, Any],
    *,
    metric: float | None = None,
    threshold: float | None = None,
    evidence: dict[str, Any] | None = None,
    rounds: list | None = None,
) -> Finding:
    copy = messages.render(rule_id, match_id, context)
    payload = dict(evidence or {})
    if rounds is not None:
        payload["rounds"] = _round_list(rounds)
    payload["label"] = messages.label(rule_id)
    return Finding(
        rule_id=rule_id,
        category=category,
        severity=severity,
        title=copy.title,
        detail=copy.detail,
        recommendation=copy.recommendation,
        metric=metric,
        threshold=threshold,
        evidence=payload,
        label=messages.label(rule_id),
    )


def evaluate(match: MatchData, metrics: dict) -> list[Finding]:
    rounds = match.rounds
    total = len(rounds)
    if total == 0:
        return []

    findings: list[Finding] = []
    match_id = match.match_id or "sin-id"
    deaths = match.overall.deaths or sum(r.deaths for r in rounds)

    fd_rounds = [r for r in rounds if r.first_death]
    fd_rate = float(metrics.get("fd_rate", 0) or 0)
    if len(fd_rounds) >= 4 and fd_rate >= 20:
        findings.append(
            _build(
                match_id,
                "first_death_rate",
                "Duelos",
                4,
                {"count": len(fd_rounds), "total": total, "rate": fd_rate},
                metric=fd_rate,
                threshold=20,
                rounds=fd_rounds,
            )
        )

    attack = [r for r in rounds if r.side == "attack"]
    attack_fd = [r for r in attack if r.first_death]
    fd_attack_rate = float(metrics.get("fd_attack_rate", 0) or 0)
    if len(attack) >= 5 and len(attack_fd) >= 3 and fd_attack_rate >= 25:
        findings.append(
            _build(
                match_id,
                "first_death_attack",
                "Duelos",
                3,
                {
                    "count": len(attack_fd),
                    "rounds": len(attack),
                    "rate": fd_attack_rate,
                },
                metric=fd_attack_rate,
                threshold=25,
                rounds=attack_fd,
            )
        )

    untraded = [r for r in rounds if r.deaths > 0 and not r.traded_death]
    trade_rate = float(metrics.get("trade_rate", 0) or 0)
    if deaths >= 8 and trade_rate < 35:
        findings.append(
            _build(
                match_id,
                "untraded_deaths",
                "Duelos",
                3,
                {"trade": trade_rate, "count": len(untraded)},
                metric=trade_rate,
                threshold=35,
                rounds=untraded,
            )
        )

    adr = float(metrics.get("adr", 0) or 0)
    damage_per_death = float(metrics.get("damage_per_death", 0) or 0)
    dpr = float(metrics.get("dpr", 0) or 0)
    if (
        deaths >= 8
        and adr >= 100
        and dpr >= 0.7
        and 0 < damage_per_death < 95
    ):
        findings.append(
            _build(
                match_id,
                "death_without_damage",
                "Duelos",
                2,
                {"damage_per_death": damage_per_death, "deaths": deaths},
                metric=damage_per_death,
                threshold=95,
            )
        )

    clutch_attempts = int(metrics.get("clutch_attempts", 0) or 0)
    clutch_wins = int(metrics.get("clutch_wins", 0) or 0)
    clutch_rate = float(metrics.get("clutch_rate", 0) or 0)
    if clutch_attempts >= 2 and clutch_rate < 34:
        findings.append(
            _build(
                match_id,
                "clutch_failures",
                "Duelos",
                2,
                {
                    "wins": clutch_wins,
                    "attempts": clutch_attempts,
                    "rate": clutch_rate,
                },
                metric=clutch_rate,
                threshold=34,
            )
        )

    deaths_with_time = int(metrics.get("deaths_with_time", 0) or 0)
    late_deaths = int(metrics.get("late_deaths", 0) or 0)
    if deaths_with_time >= 5 and late_deaths >= 3:
        findings.append(
            _build(
                match_id,
                "late_deaths",
                "Duelos",
                2,
                {"count": late_deaths, "deaths": deaths},
                metric=float(late_deaths),
                threshold=3,
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
            _build(
                match_id,
                "attack_no_utility",
                "Utilidad",
                4,
                {"zero": len(zero_util), "known": len(known_attack)},
                metric=float(len(zero_util)),
                threshold=3,
                rounds=zero_util,
            )
        )

    known_defense = [
        r
        for r in rounds
        if r.side == "defense" and r.abilities_used is not None and r.loadout_value >= 1500
    ]
    zero_util_defense = [r for r in known_defense if r.abilities_used == 0]
    if len(known_defense) >= 4 and len(zero_util_defense) >= 3:
        findings.append(
            _build(
                match_id,
                "defense_no_utility",
                "Utilidad",
                3,
                {"zero": len(zero_util_defense), "known": len(known_defense)},
                metric=float(len(zero_util_defense)),
                threshold=3,
                rounds=zero_util_defense,
            )
        )

    ult_usage = float(metrics.get("ult_usage", 0) or 0)
    if total >= 10 and ult_usage <= 5:
        findings.append(
            _build(
                match_id,
                "ult_hoarding",
                "Utilidad",
                2,
                {"usage": ult_usage, "rounds": total},
                metric=ult_usage,
                threshold=5,
            )
        )

    force_buys = int(metrics.get("force_buys", 0) or 0)
    if force_buys >= 3:
        findings.append(
            _build(
                match_id,
                "force_buy_after_loss",
                "Economía",
                3,
                {"count": force_buys},
                metric=float(force_buys),
                threshold=3,
                rounds=[r for r in rounds if r.buy_type == "force"],
            )
        )

    buy_rounds = metrics.get("buy_rounds") or {}
    buy_wins = metrics.get("buy_wins") or {}
    buy_winrate = metrics.get("buy_winrate") or {}
    force_rounds = int(buy_rounds.get("force", 0) or 0)
    force_winrate = float(buy_winrate.get("force", 0) or 0)
    if force_rounds >= 3 and force_winrate < 30:
        findings.append(
            _build(
                match_id,
                "force_buy_ineffective",
                "Economía",
                3,
                {
                    "rounds": force_rounds,
                    "wins": int(buy_wins.get("force", 0) or 0),
                    "rate": force_winrate,
                },
                metric=force_winrate,
                threshold=30,
                rounds=[r for r in rounds if r.buy_type == "force"],
            )
        )

    full_rounds = int(buy_rounds.get("full", 0) or 0)
    full_winrate = float(buy_winrate.get("full", 0) or 0)
    if full_rounds >= 6 and full_winrate < 45:
        findings.append(
            _build(
                match_id,
                "full_buy_bleed",
                "Economía",
                3,
                {
                    "rounds": full_rounds,
                    "wins": int(buy_wins.get("full", 0) or 0),
                    "rate": full_winrate,
                },
                metric=full_winrate,
                threshold=45,
                rounds=[r for r in rounds if r.buy_type == "full"],
            )
        )

    cheap_rounds = [
        r for r in rounds if r.buy_type == "save" and r.loadout_value >= 1500
    ]
    if len(cheap_rounds) >= 2:
        findings.append(
            _build(
                match_id,
                "half_buys",
                "Economía",
                2,
                {"count": len(cheap_rounds)},
                metric=float(len(cheap_rounds)),
                threshold=2,
                rounds=cheap_rounds,
            )
        )

    no_armor_buys = int(metrics.get("no_armor_buys", 0) or 0)
    if no_armor_buys >= 2:
        armor_rounds = [
            r for r in rounds if not r.has_armor and r.loadout_value >= 2000
        ]
        findings.append(
            _build(
                match_id,
                "buy_without_armor",
                "Economía",
                2,
                {"count": len(armor_rounds)},
                metric=float(len(armor_rounds)),
                threshold=2,
                rounds=armor_rounds,
            )
        )

    by_number = {r.number: r for r in rounds}
    anti_eco = [
        r
        for r in rounds
        if r.number in (2, 14)
        and (previous := by_number.get(r.number - 1)) is not None
        and previous.won
    ]
    anti_eco_losses = [r for r in anti_eco if not r.won]
    if len(anti_eco) >= 2 and len(anti_eco_losses) >= 2:
        findings.append(
            _build(
                match_id,
                "anti_eco_letdown",
                "Economía",
                3,
                {"count": len(anti_eco_losses), "rounds": len(anti_eco)},
                metric=float(len(anti_eco_losses)),
                threshold=2,
                rounds=anti_eco_losses,
            )
        )

    kast = float(metrics.get("kast", 0) or 0)
    if total >= 8 and kast < 65:
        findings.append(
            _build(
                match_id,
                "low_kast",
                "Impacto",
                3,
                {"kast": kast},
                metric=kast,
                threshold=65,
            )
        )

    hs_pct = float(metrics.get("hs_pct", 0) or 0)
    if total >= 8 and hs_pct < 20:
        findings.append(
            _build(
                match_id,
                "low_headshot_pct",
                "Aim",
                2,
                {"hs": hs_pct},
                metric=hs_pct,
                threshold=20,
            )
        )

    if total >= 8 and adr < 120:
        findings.append(
            _build(
                match_id,
                "low_adr",
                "Impacto",
                3,
                {"adr": adr},
                metric=adr,
                threshold=120,
            )
        )

    kpr = float(metrics.get("kpr", 0) or 0)
    fb_rate = float(metrics.get("fb_rate", 0) or 0)
    if total >= 10 and kpr < 0.6 and fb_rate < 12:
        findings.append(
            _build(
                match_id,
                "low_individual_impact",
                "Impacto",
                3,
                {"kpr": kpr, "fb": fb_rate},
                metric=kpr,
                threshold=0.6,
            )
        )

    lost_carry = [
        r for r in rounds if not r.won and (r.kills >= 3 or r.damage >= 200)
    ]
    if len(lost_carry) >= 2:
        findings.append(
            _build(
                match_id,
                "lost_carry_rounds",
                "Impacto",
                3,
                {"count": len(lost_carry)},
                metric=float(len(lost_carry)),
                threshold=2,
                rounds=lost_carry,
            )
        )

    damage_cv = float(metrics.get("damage_cv", 0) or 0)
    round_damage = [r.damage for r in rounds]
    if total >= 10 and damage_cv >= 65 and adr >= 100 and round_damage:
        findings.append(
            _build(
                match_id,
                "irregular_form",
                "Impacto",
                2,
                {
                    "cv": damage_cv,
                    "best": max(round_damage),
                    "worst": min(round_damage),
                },
                metric=damage_cv,
                threshold=65,
            )
        )

    adr_win = float(metrics.get("adr_win", 0) or 0)
    adr_loss = float(metrics.get("adr_loss", 0) or 0)
    loss_rounds = int(metrics.get("loss_rounds", 0) or 0)
    if (
        loss_rounds >= 4
        and adr_loss < 110
        and adr_win - adr_loss >= 45
    ):
        findings.append(
            _build(
                match_id,
                "adr_drop_in_losses",
                "Impacto",
                2,
                {
                    "adr_win": adr_win,
                    "adr_loss": adr_loss,
                    "losses": loss_rounds,
                },
                metric=adr_loss,
                threshold=110,
            )
        )

    attack_winrate = float(metrics.get("attack_winrate", 0) or 0)
    attack_rounds = int(metrics.get("attack_rounds", 0) or 0)
    if attack_rounds >= 5 and attack_winrate < 40:
        findings.append(
            _build(
                match_id,
                "weak_attack_side",
                "Lados",
                3,
                {"rate": attack_winrate, "rounds": attack_rounds},
                metric=attack_winrate,
                threshold=40,
            )
        )

    defense_winrate = float(metrics.get("defense_winrate", 0) or 0)
    defense_rounds = int(metrics.get("defense_rounds", 0) or 0)
    if defense_rounds >= 5 and defense_winrate < 40:
        findings.append(
            _build(
                match_id,
                "weak_defense_side",
                "Lados",
                3,
                {"rate": defense_winrate, "rounds": defense_rounds},
                metric=defense_winrate,
                threshold=40,
            )
        )

    pistol = [r for r in rounds if r.number in (1, 13)]
    pistol_wins = [r for r in pistol if r.won]
    if len(pistol) >= 2 and not pistol_wins:
        findings.append(
            _build(
                match_id,
                "pistol_weak",
                "Lados",
                2,
                {"wins": 0, "rounds": len(pistol)},
                metric=0.0,
                threshold=1,
                rounds=pistol,
            )
        )

    timeouts = [
        r for r in attack if not r.won and "time" in (r.reason or "").lower()
    ]
    if len(timeouts) >= 2:
        findings.append(
            _build(
                match_id,
                "attack_timeouts",
                "Lados",
                3,
                {"count": len(timeouts), "rounds": len(attack)},
                metric=float(len(timeouts)),
                threshold=2,
                rounds=timeouts,
            )
        )

    first_half_rate = float(metrics.get("first_half_rate", 0) or 0)
    second_half_rate = float(metrics.get("second_half_rate", 0) or 0)
    half_rounds = int(metrics.get("half_rounds", 0) or 0)
    if (
        half_rounds >= 3
        and first_half_rate - second_half_rate >= 30
    ):
        findings.append(
            _build(
                match_id,
                "second_half_drop",
                "Lados",
                3,
                {
                    "first_rate": first_half_rate,
                    "second_rate": second_half_rate,
                },
                metric=round(first_half_rate - second_half_rate, 1),
                threshold=30,
            )
        )

    findings.sort(key=lambda f: (f.severity, f.metric or 0), reverse=True)
    return findings[:8]
