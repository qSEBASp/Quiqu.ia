from datetime import datetime, timezone

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from .analysis.llm import LLMUnavailable, enhance_report
from .analysis.metrics import compute_metrics
from .analysis.report import build_report
from .analysis.rules import evaluate
from .analysis.strengths import evaluate_strengths
from .config import settings
from .models import Insight, Match, Profile, Report, utcnow
from .providers import ProviderError, build_provider
from .providers.base import MatchData, OverallStats, RoundData


def _iso(value: datetime | None) -> str | None:
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.isoformat()


def get_or_create_profile(db: Session) -> Profile:
    profile = db.get(Profile, 1)
    if profile is None:
        profile = Profile(
            id=1,
            provider=settings.provider if settings.provider in ("demo", "henrik") else "demo",
            henrik_api_key=settings.henrik_api_key,
            onboarded=True,
        )
        db.add(profile)
        db.commit()
        db.refresh(profile)
    return profile


def profile_dict(profile: Profile) -> dict:
    return {
        "riot_id": profile.riot_id,
        "tag": profile.tag,
        "region": profile.region,
        "platform": profile.platform,
        "provider": profile.provider,
        "puuid": profile.puuid,
        "rank_name": profile.rank_name,
        "has_henrik_key": bool(profile.henrik_api_key),
        "has_llm_key": bool(settings.llm_api_key),
        "llm_model": settings.llm_model if settings.llm_api_key else None,
        "updated_at": _iso(profile.updated_at),
    }


async def sync_matches(db: Session, profile: Profile) -> dict:
    provider = build_provider(profile, settings.demo_match_count)

    if profile.provider == "henrik":
        account = await provider.fetch_account(profile)
        if account.puuid:
            profile.puuid = account.puuid
        profile.riot_id = account.name
        profile.tag = account.tag
        profile.region = account.region
        profile.rank_name = None
        profile.rank_tier = None
        matches = await provider.fetch_matches(profile)
    else:
        account = provider.fetch_account(profile)
        profile.puuid = account.puuid
        profile.rank_name = account.rank_name
        profile.rank_tier = account.rank_tier
        matches = provider.fetch_matches(profile)

    added = 0
    skipped = 0
    for data in matches:
        if not data.match_id or db.get(Match, data.match_id) is not None:
            skipped += 1
            continue
        _persist_match(db, data)
        added += 1

    profile.updated_at = utcnow()
    db.commit()
    return {
        "added": added,
        "skipped": skipped,
        "received": len(matches),
        "provider": profile.provider,
        "profile": profile_dict(profile),
    }


def _persist_match(db: Session, data: MatchData) -> Match:
    metrics = compute_metrics(data)
    findings = evaluate(data, metrics)
    report_data = build_report(data, metrics, findings)

    match = Match(
        id=data.match_id,
        started_at=data.started_at,
        map_name=data.map_name,
        mode=data.mode,
        queue=data.queue,
        agent=data.agent,
        agent_role=data.agent_role,
        result=data.result,
        score_us=data.score_us,
        score_them=data.score_them,
        kills=data.overall.kills,
        deaths=data.overall.deaths,
        assists=data.overall.assists,
        acs=metrics["acs"],
        adr=metrics["adr"],
        hs_pct=metrics["hs_pct"],
        kast=metrics["kast"],
        first_bloods=metrics["first_bloods"],
        first_deaths=metrics["first_deaths"],
        trade_rate=metrics["trade_rate"],
        econ_score=metrics["econ_score"],
        util_usage=metrics["util_usage"],
        scoreboard=[entry.model_dump() for entry in data.scoreboard],
        metrics=metrics,
        rounds=[r.model_dump() for r in data.rounds],
        raw={
            "duration_min": data.duration_min,
            "puuid": data.puuid,
            "team_id": data.team_id,
            "name": data.name,
            "tag": data.tag,
        },
        source="demo" if data.match_id.startswith("demo-") else "henrik",
    )
    db.add(match)
    db.flush()

    for finding in findings:
        db.add(
            Insight(
                match_id=match.id,
                rule_id=finding.rule_id,
                category=finding.category,
                severity=finding.severity,
                title=finding.title,
                detail=finding.detail,
                recommendation=finding.recommendation,
                evidence=finding.evidence,
                metric=finding.metric,
                threshold=finding.threshold,
            )
        )

    db.add(
        Report(
            match_id=match.id,
            summary=report_data["summary"],
            priorities=report_data["priorities"],
            drills=report_data["drills"],
            model=report_data["model"],
        )
    )
    return match


def _top_insight(match: Match) -> Insight | None:
    if not match.insights:
        return None
    return max(match.insights, key=lambda i: (i.severity, i.metric or 0))


def match_summary(match: Match) -> dict:
    metrics = match.metrics or {}
    top = _top_insight(match)
    return {
        "id": match.id,
        "started_at": _iso(match.started_at),
        "map": match.map_name,
        "mode": match.mode,
        "agent": match.agent,
        "agent_role": match.agent_role,
        "result": match.result,
        "score_us": match.score_us,
        "score_them": match.score_them,
        "kills": match.kills,
        "deaths": match.deaths,
        "assists": match.assists,
        "acs": match.acs,
        "adr": match.adr,
        "hs_pct": match.hs_pct,
        "kast": match.kast,
        "first_bloods": match.first_bloods,
        "first_deaths": match.first_deaths,
        "econ_score": match.econ_score,
        "form_score": metrics.get("form_score", 0),
        "trade_rate": match.trade_rate,
        "insight_count": len(match.insights),
        "top_insight": top.title if top else None,
        "top_fix": top.recommendation if top else None,
        "top_insight_category": top.category if top else None,
        "top_insight_severity": top.severity if top else None,
        "source": match.source,
    }


def match_detail(match: Match) -> dict:
    report = None
    if match.report:
        report = {
            "summary": match.report.summary,
            "priorities": match.report.priorities,
            "drills": match.report.drills,
            "model": match.report.model,
            "created_at": _iso(match.report.created_at),
        }
    return {
        **match_summary(match),
        "metrics": match.metrics,
        "scoreboard": match.scoreboard,
        "rounds": match.rounds,
        "insights": [
            {
                "id": i.id,
                "rule_id": i.rule_id,
                "category": i.category,
                "severity": i.severity,
                "title": i.title,
                "detail": i.detail,
                "recommendation": i.recommendation,
                "evidence": i.evidence,
                "metric": i.metric,
                "threshold": i.threshold,
            }
            for i in match.insights
        ],
        "strengths": [
            {
                "rule_id": s.rule_id,
                "category": s.category,
                "title": s.title,
                "summary": s.summary,
                "detail": s.detail,
                "tier": s.tier,
                "metric": s.metric,
            }
            for s in evaluate_strengths(match.metrics or {})
        ],
        "report": report,
    }


def build_overview(db: Session) -> dict:
    profile = get_or_create_profile(db)
    matches = list(
        db.scalars(select(Match).order_by(Match.started_at.desc())).all()
    )

    wins = sum(1 for m in matches if m.result == "win")
    losses = sum(1 for m in matches if m.result == "loss")
    total = len(matches)
    kills = sum(m.kills for m in matches)
    deaths = sum(m.deaths for m in matches)
    assists = sum(m.assists for m in matches)

    def avg(key: str) -> float:
        if not matches:
            return 0.0
        return round(sum(getattr(m, key) for m in matches) / len(matches), 1)

    patterns: dict[str, dict] = {}
    for match in matches:
        for insight in match.insights:
            item = patterns.setdefault(
                insight.rule_id,
                {
                    "rule_id": insight.rule_id,
                    "title": insight.title,
                    "category": insight.category,
                    "severity": insight.severity,
                    "count": 0,
                    "match_ids": [],
                },
            )
            item["count"] += 1
            item["match_ids"].append(match.id)

    top_patterns = sorted(
        patterns.values(),
        key=lambda p: (p["count"] * p["severity"], p["count"]),
        reverse=True,
    )[:5]

    strength_patterns: dict[str, dict] = {}
    for match in matches:
        for strength in evaluate_strengths(match.metrics or {}):
            item = strength_patterns.get(strength.rule_id)
            if item is None:
                item = strength_patterns[strength.rule_id] = {
                    "rule_id": strength.rule_id,
                    "title": strength.title,
                    "category": strength.category,
                    "summary": strength.summary,
                    "detail": strength.detail,
                    "tier": strength.tier,
                    "metric": None,
                    "count": 0,
                    "match_ids": [],
                }
            item["count"] += 1
            item["match_ids"].append(match.id)

    top_strengths = sorted(
        strength_patterns.values(),
        key=lambda s: (s["count"], s["tier"]),
        reverse=True,
    )[:5]

    current_streak = 0
    streak_result = None
    for match in matches:
        if streak_result is None:
            streak_result = match.result
        if match.result != streak_result:
            break
        current_streak += 1

    trend = [
        {
            "id": m.id,
            "date": _iso(m.started_at),
            "acs": m.acs,
            "hs_pct": m.hs_pct,
            "kast": m.kast,
            "result": m.result,
            "map": m.map_name,
            "agent": m.agent,
        }
        for m in reversed(matches[:15])
    ]

    return {
        "profile": profile_dict(profile),
        "totals": {
            "matches": total,
            "wins": wins,
            "losses": losses,
            "winrate": round(wins / total * 100, 1) if total else 0.0,
            "kd": round(kills / max(1, deaths), 2),
            "kills": kills,
            "deaths": deaths,
            "assists": assists,
            "acs": avg("acs"),
            "adr": avg("adr"),
            "hs_pct": avg("hs_pct"),
            "kast": avg("kast"),
            "form_score": round(
                sum((m.metrics or {}).get("form_score", 0) for m in matches) / total, 1
            )
            if total
            else 0.0,
            "current_streak": current_streak,
            "streak_result": streak_result,
        },
        "top_patterns": top_patterns,
        "strengths": top_strengths,
        "trend": trend,
        "recent": [match_summary(m) for m in matches[:6]],
    }


def list_matches(db: Session, limit: int = 100) -> list[dict]:
    matches = db.scalars(
        select(Match).order_by(Match.started_at.desc()).limit(min(limit, 200))
    ).all()
    return [match_summary(m) for m in matches]


def reset_data(db: Session) -> None:
    db.execute(delete(Insight))
    db.execute(delete(Report))
    db.execute(delete(Match))
    db.commit()


def _rounds_from_json(rows: list[dict]) -> list[RoundData]:
    return [RoundData(**row) for row in rows]


def regenerate_report(db: Session, match: Match) -> dict:
    rounds = _rounds_from_json(match.rounds or [])
    total = max(1, len(rounds))
    match_data = MatchData(
        match_id=match.id,
        started_at=match.started_at,
        map_name=match.map_name,
        mode=match.mode,
        queue=match.queue,
        agent=match.agent,
        agent_role=match.agent_role,
        result=match.result,
        score_us=match.score_us,
        score_them=match.score_them,
        overall=OverallStats(
            kills=match.kills,
            deaths=match.deaths,
            assists=match.assists,
            score=int(match.acs * total),
            damage_dealt=int(match.adr * total),
        ),
        rounds=rounds,
    )
    metrics = match.metrics or compute_metrics(match_data)
    findings = evaluate(match_data, metrics)
    enhanced = enhance_report(match_data, metrics, findings)

    report = match.report
    if report is None:
        report = Report(match_id=match.id, summary="", priorities=[], drills=[], model="rules")
        db.add(report)
    report.summary = enhanced["summary"]
    report.priorities = enhanced["priorities"]
    report.drills = enhanced["drills"]
    report.model = enhanced["model"]
    report.created_at = utcnow()
    db.commit()
    db.refresh(match)
    return {
        "summary": report.summary,
        "priorities": report.priorities,
        "drills": report.drills,
        "model": report.model,
        "created_at": _iso(report.created_at),
    }
