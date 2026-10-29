from datetime import datetime, timezone

from app.analysis.metrics import compute_metrics
from app.analysis.rules import evaluate
from app.providers.base import MatchData, OverallStats, RoundData


def make_round(
    number: int,
    *,
    side: str = "attack",
    won: bool = True,
    kills: int = 0,
    deaths: int = 0,
    assists: int = 0,
    survived: bool = True,
    traded: bool = False,
    loadout: int = 4000,
    armor: bool = True,
    buy_type: str = "full",
    abilities: int | None = 2,
    first_blood: bool = False,
    first_death: bool = False,
    damage: int = 100,
    reason: str = "Elimination",
) -> RoundData:
    return RoundData(
        number=number,
        side=side,
        won=won,
        reason=reason,
        kills=kills,
        deaths=deaths,
        assists=assists,
        survived=survived,
        traded_death=traded,
        loadout_value=loadout,
        has_armor=armor,
        buy_type=buy_type,
        abilities_used=abilities,
        first_blood=first_blood,
        first_death=first_death,
        damage=damage,
        headshots=2,
        bodyshots=8,
        legshots=0,
    )


def make_match(rounds: list[RoundData], **overall) -> MatchData:
    return MatchData(
        match_id="test-match",
        started_at=datetime(2026, 10, 20, tzinfo=timezone.utc),
        map_name="Ascent",
        agent="Omen",
        overall=OverallStats(**overall),
        rounds=rounds,
    )


def sample_match() -> MatchData:
    return make_match(
        [
            make_round(1, won=True, kills=1, first_blood=True, abilities=2),
            make_round(2, won=True, kills=1, abilities=0),
            make_round(3, won=False, deaths=1, survived=False, traded=True, abilities=0),
            make_round(
                4,
                won=False,
                deaths=1,
                survived=False,
                loadout=2500,
                buy_type="force",
                abilities=None,
                first_death=True,
            ),
            make_round(5, won=True, abilities=0),
            make_round(6, side="defense", won=True, kills=1, abilities=1, first_blood=True),
            make_round(7, side="defense", won=True, abilities=1),
            make_round(
                8,
                side="defense",
                won=False,
                deaths=1,
                survived=False,
                loadout=2500,
                armor=False,
                buy_type="force",
                abilities=0,
                first_death=True,
            ),
            make_round(9, side="defense", won=False, deaths=1, survived=False, abilities=0),
            make_round(10, side="defense", won=False, deaths=1, survived=False, abilities=None),
        ],
        kills=10,
        deaths=10,
        assists=5,
        score=2600,
        damage_dealt=2000,
        headshots=20,
        bodyshots=60,
        legshots=20,
    )


def test_metrics_compute_core_stats():
    metrics = compute_metrics(sample_match())

    assert metrics["rounds"] == 10
    assert metrics["acs"] == 260.0
    assert metrics["adr"] == 200.0
    assert metrics["hs_pct"] == 20.0
    assert metrics["kast"] == 60.0
    assert metrics["kd"] == 1.0
    assert metrics["kpr"] == 1.0
    assert metrics["dpr"] == 1.0
    assert metrics["trade_rate"] == 10.0
    assert metrics["first_bloods"] == 2
    assert metrics["first_deaths"] == 2
    assert metrics["fb_rate"] == 20.0
    assert metrics["fd_rate"] == 20.0
    assert metrics["force_buys"] == 1
    assert metrics["no_armor_buys"] == 1
    assert metrics["econ_score"] == 83.0
    assert metrics["attack_rounds"] == 5
    assert metrics["defense_rounds"] == 5
    assert metrics["attack_winrate"] == 60.0
    assert metrics["defense_winrate"] == 40.0
    assert metrics["form_score"] == 100.0


def test_util_usage_ignores_unknown_abilities():
    metrics = compute_metrics(sample_match())

    # Rounds 4 and 10 no traen ability_casts: no cuentan como cero.
    assert metrics["util_rounds_known"] == 4
    assert metrics["util_usage"] == 0.5


def test_no_utility_rule_fires_with_partial_data():
    ids = {f.rule_id for f in evaluate(sample_match(), compute_metrics(sample_match()))}

    assert "attack_no_utility" in ids
    assert "low_kast" in ids
    assert "untraded_deaths" in ids


def test_no_utility_rule_skipped_when_casts_are_unknown():
    rounds = [
        make_round(number, won=number % 2 == 0, abilities=None, loadout=4200)
        for number in range(1, 11)
    ]
    match = make_match(rounds, kills=5, deaths=5, score=1500, damage_dealt=1400)
    metrics = compute_metrics(match)

    assert metrics["util_rounds_known"] == 0
    assert metrics["util_usage"] == 0.0
    assert "attack_no_utility" not in {f.rule_id for f in evaluate(match, metrics)}


def test_no_utility_rule_needs_enough_known_rounds():
    rounds = [
        make_round(1, abilities=0),
        make_round(2, abilities=0),
        make_round(3, abilities=0),
        *[make_round(number, abilities=None) for number in range(4, 11)],
    ]
    match = make_match(rounds, kills=5, deaths=5, score=1500, damage_dealt=1400)
    metrics = compute_metrics(match)

    assert metrics["util_rounds_known"] == 3
    assert "attack_no_utility" not in {f.rule_id for f in evaluate(match, metrics)}


def test_late_deaths_rule_needs_kill_events():
    rounds = [
        make_round(number, won=number % 2 == 0, deaths=1, survived=False)
        for number in range(1, 11)
    ]
    match = make_match(rounds, kills=5, deaths=10, score=1500, damage_dealt=1200)
    metrics = compute_metrics(match)

    assert metrics["deaths_with_time"] == 0
    assert metrics["late_deaths"] == 0
    assert "late_deaths" not in {f.rule_id for f in evaluate(match, metrics)}


def test_second_half_drop_fires_when_the_second_half_collapses():
    rounds = [
        make_round(
            number,
            won=number <= 6,
            side="attack" if number <= 12 else "defense",
            kills=1,
        )
        for number in range(1, 19)
    ]
    match = make_match(rounds, kills=18, deaths=6, score=3000, damage_dealt=2600)
    metrics = compute_metrics(match)
    ids = {f.rule_id for f in evaluate(match, metrics)}

    assert metrics["first_half_rate"] == 50.0
    assert metrics["second_half_rate"] == 0.0
    assert "second_half_drop" in ids


def test_second_half_rule_skipped_when_halves_are_similar():
    rounds = [
        make_round(number, won=number % 2 == 0, kills=1)
        for number in range(1, 19)
    ]
    match = make_match(rounds, kills=18, deaths=6, score=3000, damage_dealt=2600)
    metrics = compute_metrics(match)

    assert metrics["first_half_rate"] == metrics["second_half_rate"]
    assert "second_half_drop" not in {f.rule_id for f in evaluate(match, metrics)}


def test_attack_timeouts_need_lost_attack_rounds():
    rounds = [
        make_round(1, won=False, reason="Time expired"),
        make_round(2, won=False, reason="Time expired"),
        make_round(3, won=True, reason="Spike detonated"),
    ]
    match = make_match(rounds, kills=3, deaths=4, score=900, damage_dealt=800)
    metrics = compute_metrics(match)

    assert metrics["attack_timeouts"] == 2
    assert "attack_timeouts" in {f.rule_id for f in evaluate(match, metrics)}


def test_anti_eco_rule_needs_lost_round_after_pistol_win():
    rounds = [
        make_round(1, won=True, kills=2),
        make_round(2, won=False, deaths=1, survived=False),
        make_round(3, won=True),
        make_round(4, won=False, deaths=1, survived=False),
    ]
    match = make_match(rounds, kills=4, deaths=3, score=600, damage_dealt=500)
    metrics = compute_metrics(match)

    assert metrics["anti_eco_rounds"] == 1
    assert metrics["anti_eco_losses"] == 1
    # Con una sola anti-eco no hay patron suficiente.
    assert "anti_eco_letdown" not in {f.rule_id for f in evaluate(match, metrics)}
