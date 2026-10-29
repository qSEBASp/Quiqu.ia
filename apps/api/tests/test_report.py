from datetime import datetime, timezone

from app.analysis.report import MAX_PRIORITIES, build_report
from app.analysis.rules import Finding
from app.providers.base import MatchData, OverallStats


def make_match() -> MatchData:
    return MatchData(
        match_id="report-match",
        started_at=datetime(2026, 10, 20, tzinfo=timezone.utc),
        map_name="Ascent",
        agent="Omen",
        result="win",
        score_us=13,
        score_them=7,
        overall=OverallStats(kills=18, deaths=12, assists=6, score=3800, damage_dealt=2600),
    )


def make_metrics() -> dict:
    return {
        "rounds": 20,
        "acs": 190.0,
        "adr": 130.0,
        "hs_pct": 18.0,
        "kast": 66.0,
        "kd": 1.5,
        "dpr": 0.6,
        "trade_rate": 30.0,
        "fb_rate": 10.0,
        "fd_rate": 22.0,
        "econ_score": 60.0,
        "util_usage": 0.0,
        "util_rounds_known": 0,
        "attack_rounds": 10,
        "defense_rounds": 10,
        "attack_winrate": 35.0,
        "defense_winrate": 45.0,
        "form_score": 55.0,
    }


def finding(
    index: int,
    category: str,
    severity: int,
    *,
    fix: str = "Acción concreta",
) -> Finding:
    return Finding(
        rule_id=f"rule-{index}",
        category=category,
        severity=severity,
        title=f"Título {index}",
        detail=f"Detalle {index}",
        recommendation=fix,
        label=f"Etiqueta {index}",
    )


def test_report_caps_priorities_and_categories():
    findings = [
        finding(1, "Duelos", 2),
        finding(2, "Economía", 5),
        finding(3, "Duelos", 4),
        finding(4, "Economía", 4),
        finding(5, "Impacto", 3),
        finding(6, "Duelos", 3),
        finding(7, "Impacto", 2),
        finding(8, "Lados", 5),
        finding(9, "Lados", 1),
    ]
    report = build_report(make_match(), make_metrics(), findings)

    assert len(report["priorities"]) == MAX_PRIORITIES
    counts: dict[str, int] = {}
    for priority in report["priorities"]:
        counts[priority["category"]] = counts.get(priority["category"], 0) + 1
    assert all(count <= 2 for count in counts.values())
    # Las dos de mayor severidad siempre entran.
    assert {"rule-2", "rule-8"} <= {
        priority["rule_id"] for priority in report["priorities"]
    }


def test_report_drills_do_not_repeat_fixes():
    fix = "10 minutos de deathmatch buscando solo primeros contactos."
    findings = [
        finding(1, "Duelos", 4, fix=fix),
        finding(2, "Impacto", 3, fix="Juega una partida midiendo KAST."),
    ]
    report = build_report(make_match(), make_metrics(), findings)

    assert len(report["drills"]) == 3
    fixes = {finding.recommendation.lower() for finding in findings}
    assert all(drill.lower() not in fixes for drill in report["drills"])


def test_clean_report_has_summary_and_drills():
    report = build_report(make_match(), make_metrics(), [])

    assert report["priorities"] == []
    assert report["summary"]
    assert len(report["drills"]) == 3
    assert report["model"] == "rules"


def test_report_summary_changes_between_matches():
    metrics = make_metrics()
    findings = [finding(1, "Duelos", 4), finding(2, "Economía", 3)]
    summaries = set()
    for match_id in ("demo-01", "demo-02", "demo-03"):
        match = make_match()
        match.match_id = match_id
        summaries.add(build_report(match, metrics, findings)["summary"])
    assert len(summaries) >= 2
