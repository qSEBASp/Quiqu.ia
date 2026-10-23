from ..providers.base import MatchData


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


BUY_TYPES = ("full", "force", "save", "unknown")


def _economy_stats(rounds: list) -> dict:
    rounds_by_buy = {key: 0 for key in BUY_TYPES}
    wins_by_buy = {key: 0 for key in BUY_TYPES}
    for r in rounds:
        buy = r.buy_type if r.buy_type in BUY_TYPES else "unknown"
        rounds_by_buy[buy] += 1
        if r.won:
            wins_by_buy[buy] += 1

    def winrate(key: str) -> float:
        played = rounds_by_buy[key]
        return round(wins_by_buy[key] / played * 100, 1) if played else 0.0

    total = max(1, len(rounds))
    return {
        "buy_rounds": rounds_by_buy,
        "buy_wins": wins_by_buy,
        "buy_winrate": {key: winrate(key) for key in BUY_TYPES},
        "avg_loadout": round(sum(r.loadout_value for r in rounds) / total, 0),
        "avg_credits": round(sum(r.credits_remaining for r in rounds) / total, 0),
        "save_winrate": winrate("save"),
        "force_winrate": winrate("force"),
        "full_winrate": winrate("full"),
    }


def _clutch_stats(match: MatchData, rounds: list) -> dict:
    """Clutches 1vX calculadas desde los eventos de kill.

    Solo se pueden calcular si el proveedor expone equipos en los kills. Si no
    hay datos suficientes devolvemos ceros en lugar de inventar situaciones.
    """
    zero = {
        "clutch_attempts": 0,
        "clutch_wins": 0,
        "clutch_rate": 0.0,
        "clutch_kills": 0,
    }
    if not match.kills or not rounds:
        return zero

    my_team = match.team_id
    if not my_team:
        for kill in match.kills:
            if kill.killer_puuid == match.puuid and kill.killer_team:
                my_team = kill.killer_team
                break
            if kill.victim_puuid == match.puuid and kill.victim_team:
                my_team = kill.victim_team
                break
    if not my_team:
        return zero

    by_round: dict[int, list] = {}
    for kill in match.kills:
        by_round.setdefault(kill.round, []).append(kill)

    attempts = 0
    wins = 0
    clutch_kills = 0

    for round_data in rounds:
        events = (
            by_round.get(round_data.number)
            or by_round.get(round_data.number - 1)
            or []
        )
        if not events:
            continue
        labels = {
            label
            for kill in events
            for label in (kill.killer_team, kill.victim_team)
            if label
        }
        enemies = labels - {my_team}
        if not enemies:
            continue

        alive = {my_team: 5}
        for enemy in enemies:
            alive[enemy] = 5

        in_clutch = False
        for kill in sorted(events, key=lambda k: k.time_ms):
            victim_team = kill.victim_team
            if not victim_team and kill.victim_puuid == match.puuid:
                victim_team = my_team
            if not victim_team:
                continue
            alive[victim_team] = max(0, alive.get(victim_team, 5) - 1)

            my_alive = alive.get(my_team, 5)
            enemies_alive = sum(
                value for team, value in alive.items() if team != my_team
            )
            if my_alive == 1 and enemies_alive >= 2:
                in_clutch = True
            if kill.killer_puuid == match.puuid and in_clutch:
                clutch_kills += 1

        if in_clutch:
            attempts += 1
            if round_data.won:
                wins += 1

    return {
        "clutch_attempts": attempts,
        "clutch_wins": wins,
        "clutch_rate": round(wins / attempts * 100, 1) if attempts else 0.0,
        "clutch_kills": clutch_kills,
    }


def _key_rounds(rounds: list) -> list[dict]:
    impactful = [
        r
        for r in rounds
        if r.kills >= 3 or (r.won and r.kills >= 2 and r.damage >= 200)
    ]
    impactful.sort(key=lambda r: (r.kills, r.damage, r.won), reverse=True)
    return [
        {
            "number": r.number,
            "side": r.side,
            "won": r.won,
            "kills": r.kills,
            "deaths": r.deaths,
            "damage": r.damage,
            "reason": r.reason,
        }
        for r in impactful[:6]
    ]


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
            "buy_rounds": {key: 0 for key in BUY_TYPES},
            "buy_wins": {key: 0 for key in BUY_TYPES},
            "buy_winrate": {key: 0.0 for key in BUY_TYPES},
            "avg_loadout": 0,
            "avg_credits": 0,
            "save_winrate": 0.0,
            "force_winrate": 0.0,
            "full_winrate": 0.0,
            "clutch_attempts": 0,
            "clutch_wins": 0,
            "clutch_rate": 0.0,
            "clutch_kills": 0,
            "key_rounds": [],
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
        **_economy_stats(rounds),
        **_clutch_stats(match, rounds),
        "key_rounds": _key_rounds(rounds),
    }
