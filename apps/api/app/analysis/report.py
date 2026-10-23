from ..providers.base import MatchData
from .llm import LLMUnavailable, enhance_report
from .rules import Finding
from .strengths import evaluate_strengths


def _strengths(metrics: dict) -> list[str]:
    return [strength.title.lower() for strength in evaluate_strengths(metrics)][:2]


def build_report(
    match: MatchData,
    metrics: dict,
    findings: list[Finding],
    prefer_llm: bool = False,
) -> dict:
    result = "Victoria" if match.result == "win" else "Derrota" if match.result == "loss" else "Empate"
    strengths = _strengths(metrics)
    strength_text = (
        f"Punto fuerte: {', '.join(strengths)}." if strengths else "Sin un punto fuerte claro esta partida."
    )

    if findings:
        summary = (
            f"{result} {match.score_us}-{match.score_them} en {match.map_name} con {match.agent}. "
            f"{match.overall.kills}/{match.overall.deaths}/{match.overall.assists}, "
            f"{metrics['acs']:.0f} ACS y {metrics['kast']:.0f}% KAST. {strength_text} "
            f"Prioridad: {findings[0].title.lower()}."
        )
        priorities = [
            {
                "rule_id": f.rule_id,
                "title": f.title,
                "category": f.category,
                "severity": f.severity,
                "why": f.detail,
                "fix": f.recommendation,
                "evidence": f.evidence,
            }
            for f in findings[:4]
        ]
        drills = []
        for finding in findings[:4]:
            if finding.recommendation not in drills:
                drills.append(finding.recommendation)
    else:
        summary = (
            f"{result} {match.score_us}-{match.score_them} en {match.map_name} con {match.agent}. "
            f"{match.overall.kills}/{match.overall.deaths}/{match.overall.assists} y "
            f"{metrics['acs']:.0f} ACS. {strength_text} No hay errores graves repetidos: "
            "mantén esta base y sube el nivel de dificultad de los duelos que eliges."
        )
        priorities = []
        drills = [
            "Revisa una ronda perdida por partida y anota por qué la perdiste.",
            "Mantén la misma rutina de calentamiento antes de jugar.",
        ]

    report = {
        "summary": summary,
        "priorities": priorities,
        "drills": drills[:3],
        "model": "rules",
    }

    if prefer_llm:
        try:
            enhanced = enhance_report(match, metrics, findings)
            report = {
                "summary": enhanced["summary"],
                "priorities": enhanced["priorities"],
                "drills": enhanced["drills"],
                "model": enhanced["model"],
            }
        except LLMUnavailable:
            pass

    return report
