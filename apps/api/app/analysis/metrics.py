from ..providers.base import MatchData


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def compute_metrics(match: MatchData) -> dict:
    rounds = match.rounds
    total = len(rounds)
    if total == 0:
        return {
            "rounds": 0,
            "acs": 0.0,
            "adr": 0.0,
            "hs_pct": 0.0,
            "kast": 0.0,
            "kd": 0.0,
            "trade_rate": 0.0,
            "fb_rate": 0.0,
            "fd_rate": 0.0,
            "util_usage": 0.0,
            "util_rounds_known": 0,
            "ult_usage": 0.0,
            "force_buys": 0,
            "no_armor_buys": 0,
            "econ_score": 0.0,
            "form_score": 0.0,
            "attack_rounds": 0,
            "defense_rounds": 0,
            "attack_winrate": 0.0,
            "defense_winrate": 0.0,
            "kpr": 0.0,
            "dpr": 0.0,
        }

    attack = [r for r in rounds if r.side == "attack"]
    defense = [r for r in rounds if r.side == "defense"]
    overall = match.overall

    shots = overall.headshots + overall.bodyshots + overall.legshots
    if shots == 0:
        shots = sum(r.headshots + r.bodyshots + r.legshots for r in rounds)
        headshots = sum(r.headshots for r in rounds)
    else:
        headshots = overall.headshots

    kast_rounds = sum(
        1 for r in rounds if r.kills > 0 or r.assists > 0 or r.survived or r.traded_death
    )
    deaths = overall.deaths or sum(r.deaths for r in rounds)
    traded = sum(1 for r in rounds if r.traded_death)
    first_bloods = sum(1 for r in rounds if r.first_blood)
    first_deaths = sum(1 for r in rounds if r.first_death)

    force_buys = 0
    previous_won = True
    for r in rounds:
        if r.buy_type == "force" and not previous_won:
            force_buys += 1
        previous_won = r.won

    no_armor_buys = sum(1 for r in rounds if not r.has_armor and r.loadout_value >= 2000)
    cheap_rounds = sum(
        1 for r in rounds if r.buy_type == "save" and r.loadout_value >= 1500
    )

    econ_score = _clamp(
        100 - force_buys * 7 - no_armor_buys * 10 - cheap_rounds * 4, 0, 100
    )
    attack_winrate = (
        sum(1 for r in attack if r.won) / len(attack) * 100 if attack else 0.0
    )
    defense_winrate = (
        sum(1 for r in defense if r.won) / len(defense) * 100 if defense else 0.0
    )

    kast = kast_rounds / total * 100
    acs = overall.score / total
    adr = overall.damage_dealt / total
    hs_pct = headshots / shots * 100 if shots else 0.0
    known_util = [r.abilities_used for r in attack if r.abilities_used is not None]
    util_usage = sum(known_util) / len(known_util) if known_util else 0.0
    ult_usage = sum(1 for r in rounds if r.ult_used) / total * 100
    form_score = _clamp(
        (acs / 260) * 40
        + (kast / 72) * 25
        + (hs_pct / 25) * 10
        + (adr / 160) * 25,
        0,
        100,
    )

    return {
        "rounds": total,
        "attack_rounds": len(attack),
        "defense_rounds": len(defense),
        "attack_winrate": round(attack_winrate, 1),
        "defense_winrate": round(defense_winrate, 1),
        "acs": round(acs, 1),
        "adr": round(adr, 1),
        "hs_pct": round(hs_pct, 1),
        "kast": round(kast, 1),
        "kd": round(overall.kills / max(1, deaths), 2),
        "kpr": round(overall.kills / total, 2),
        "dpr": round(deaths / total, 2),
        "trade_rate": round(traded / max(1, deaths) * 100, 1),
        "first_bloods": first_bloods,
        "first_deaths": first_deaths,
        "fb_rate": round(first_bloods / total * 100, 1),
        "fd_rate": round(first_deaths / total * 100, 1),
        "util_usage": round(util_usage, 2),
        "util_rounds_known": len(known_util),
        "ult_usage": round(ult_usage, 1),
        "force_buys": force_buys,
        "no_armor_buys": no_armor_buys,
        "econ_score": round(econ_score, 1),
        "form_score": round(form_score, 1),
    }
