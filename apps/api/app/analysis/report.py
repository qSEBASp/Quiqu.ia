from ..providers.base import MatchData
from . import messages
from .llm import LLMUnavailable, enhance_report
from .rules import Finding
from .strengths import evaluate_strengths

MAX_PRIORITIES = 5


def _strengths(metrics: dict, match_id: str) -> list[str]:
    return [
        strength.title
        for strength in evaluate_strengths(metrics, match_id)
    ][:2]


def _select(findings: list[Finding]) -> list[Finding]:
    """Prioriza severidad sin repetir cuatro veces la misma categoria."""
    selected: list[Finding] = []
    per_category: dict[str, int] = {}
    for finding in sorted(findings, key=lambda f: f.severity, reverse=True):
        if per_category.get(finding.category, 0) >= 2:
            continue
        selected.append(finding)
        per_category[finding.category] = per_category.get(finding.category, 0) + 1
        if len(selected) == MAX_PRIORITIES:
            break
    return selected


def _drills(findings: list[Finding], match_id: str) -> list[str]:
    fixes = {finding.recommendation.strip().lower() for finding in findings}
    drills = [
        drill
        for drill in messages.drills_for(findings, match_id)
        if drill.strip().lower() not in fixes
    ]
    for candidate in messages.CLEAN_DRILLS:
        if len(drills) == 3:
            break
        if candidate not in drills:
            drills.append(candidate)
    return drills[:3]


def build_report(
    match: MatchData,
    metrics: dict,
    findings: list[Finding],
    prefer_llm: bool = False,
    previous_reports: list[dict] | None = None,
) -> dict:
    result = "Victoria" if match.result == "win" else "Derrota" if match.result == "loss" else "Empate"
    match_id = match.match_id or "sin-id"
    strengths = _strengths(metrics, match_id)
    strength_text = (
        f"Punto fuerte: {', '.join(strengths)}."
        if strengths
        else "Sin un punto fuerte claro esta partida."
    )
    selected = _select(findings)
    focus = selected[0].title if selected else ""

    context = {
        "result": result,
        "us": match.score_us,
        "them": match.score_them,
        "map": match.map_name,
        "agent": match.agent,
        "kda": f"{match.overall.kills}/{match.overall.deaths}/{match.overall.assists}",
        "acs": metrics.get("acs", 0.0),
        "kast": metrics.get("kast", 0.0),
        "strength_text": strength_text,
        "focus": focus,
    }

    if selected:
        template = messages.pick_text(
            match_id, "summary", messages.FINDINGS_SUMMARIES
        )
        summary = template.format(**context)
    else:
        template = messages.pick_text(
            match_id, "summary", messages.CLEAN_SUMMARIES
        )
        summary = template.format(**context)

    priorities = [
        {
            "rule_id": finding.rule_id,
            "title": finding.title,
            "category": finding.category,
            "severity": finding.severity,
            "why": finding.detail,
            "fix": finding.recommendation,
            "evidence": finding.evidence,
        }
        for finding in selected
    ]
    drills = _drills(selected, match_id)

    report = {
        "summary": summary,
        "priorities": priorities,
        "drills": drills,
        "model": "rules",
    }

    if prefer_llm:
        try:
            enhanced = enhance_report(
                match, metrics, findings, previous_reports=previous_reports
            )
            report = {
                "summary": enhanced["summary"],
                "priorities": enhanced["priorities"],
                "drills": enhanced["drills"] or drills,
                "model": enhanced["model"],
            }
        except LLMUnavailable:
            pass

    return report
