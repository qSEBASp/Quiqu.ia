from datetime import datetime, timezone

from app.analysis.report import build_report
from app.analysis.strengths import MIN_ROUNDS, evaluate_strengths
from app.providers.base import MatchData


def metrics(**overrides) -> dict:
    base = {
        "rounds": 18,
        "acs": 200.0,
        "adr": 130.0,
        "hs_pct": 18.0,
        "kast": 68.0,
        "kd": 1.0,
        "kpr": 0.6,
        "dpr": 0.7,
        "trade_rate": 30.0,
        "fb_rate": 10.0,
        "fd_rate": 18.0,
        "econ_score": 70.0,
        "util_usage": 0.0,
        "util_rounds_known": 0,
        "ult_usage": 0.0,
        "attack_rounds": 9,
        "defense_rounds": 9,
        "attack_winrate": 45.0,
        "defense_winrate": 55.0,
        "form_score": 55.0,
    }
    base.update(overrides)
    return base


def strong_metrics() -> dict:
    return metrics(
        acs=265.0,
        adr=168.0,
        hs_pct=31.0,
        kast=82.0,
        dpr=0.5,
        trade_rate=52.0,
        fb_rate=26.0,
        fd_rate=9.0,
        econ_score=96.0,
        attack_winrate=68.0,
        defense_winrate=64.0,
    )


def test_weak_match_has_no_strengths():
    assert evaluate_strengths(metrics()) == []


def test_short_match_has_no_strengths():
    assert evaluate_strengths(strong_metrics() | {"rounds": MIN_ROUNDS - 1}) == []


def test_strong_match_returns_capped_ordered_strengths():
    strengths = evaluate_strengths(strong_metrics())

    assert 1 <= len(strengths) <= 3
    assert [s.tier for s in strengths] == sorted(
        [s.tier for s in strengths], reverse=True
    )
    assert strengths[0].rule_id in {"high_impact", "first_contact_edge"}
    for strength in strengths:
        assert strength.title
        assert strength.summary
        assert strength.detail
        assert strength.metric is not None


def test_strengths_are_deterministic():
    first = evaluate_strengths(strong_metrics())
    second = evaluate_strengths(strong_metrics())

    assert [(s.rule_id, s.metric) for s in first] == [
        (s.rule_id, s.metric) for s in second
    ]


def test_report_mentions_strength():
    match = MatchData(
        match_id="strength-match",
        started_at=datetime(2026, 10, 20, tzinfo=timezone.utc),
        map_name="Ascent",
        agent="Omen",
        score_us=13,
        score_them=9,
    )
    report = build_report(match, strong_metrics(), [])

    assert "Punto fuerte:" in report["summary"]
