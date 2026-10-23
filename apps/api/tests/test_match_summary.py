from datetime import datetime, timezone

from app.models import Insight, Match
from app.services import match_summary


def insight(title: str, severity: int, recommendation: str) -> Insight:
    return Insight(
        rule_id=title.lower().replace(" ", "_"),
        category="Aim",
        severity=severity,
        title=title,
        detail="detalle",
        recommendation=recommendation,
        evidence={},
        metric=1.0,
        threshold=1.0,
    )


def make_match(insights: list[Insight]) -> Match:
    match = Match(
        id="match-1",
        started_at=datetime(2026, 10, 20, tzinfo=timezone.utc),
        map_name="Ascent",
        agent="Omen",
        metrics={},
    )
    match.insights = insights
    return match


def test_summary_uses_highest_severity_insight():
    match = make_match(
        [
            insight("Poco daño", 2, "Juega más cerca del equipo."),
            insight("Regalas primeros contactos", 4, "No seas el primero en asomarte."),
            insight("Economía floja", 3, "Define reglas de compra."),
        ]
    )

    summary = match_summary(match)

    assert summary["top_insight"] == "Regalas primeros contactos"
    assert summary["top_fix"] == "No seas el primero en asomarte."
    assert summary["top_insight_severity"] == 4
    assert summary["top_insight_category"] == "Aim"
    assert summary["insight_count"] == 3


def test_summary_without_insights_has_no_fix():
    summary = match_summary(make_match([]))

    assert summary["top_insight"] is None
    assert summary["top_fix"] is None
    assert summary["top_insight_severity"] is None
    assert summary["insight_count"] == 0
