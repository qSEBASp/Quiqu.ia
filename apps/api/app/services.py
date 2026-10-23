from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from .analysis.benchmarks import build_benchmarks
from .analysis.llm import LLMUnavailable, enhance_report
from .analysis.metrics import compute_metrics
from .analysis.modes import normalize_mode
from .analysis.report import build_report
from .analysis.rules import evaluate
from .analysis.strengths import evaluate_strengths
from .config import settings
from .models import Goal, Insight, Match, Profile, RankSnapshot, Report, utcnow
from .providers import ProviderError, build_provider
from .providers.base import MatchData, OverallStats, RoundData


def _iso(value: datetime | None) -> str | None:
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.isoformat()


def _aware(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


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
        "rank_tier": profile.rank_tier,
        "has_henrik_key": bool(profile.henrik_api_key),
        "has_llm_key": bool(settings.llm_api_key),
        "llm_model": settings.llm_model if settings.llm_api_key else None,
        "updated_at": _iso(profile.updated_at),
    }


def _apply_rank(profile: Profile, account) -> None:
    profile.rank_name = account.rank_name
    profile.rank_tier = account.rank_tier


def _latest_rank(db: Session) -> RankSnapshot | None:
    return db.scalars(
        select(RankSnapshot).order_by(RankSnapshot.captured_at.desc()).limit(1)
    ).first()


def _record_rank(
    db: Session,
    profile: Profile,
    rr: int | None,
    last_change: int | None,
    source: str,
    captured_at: datetime | None = None,
) -> None:
    if not profile.rank_name:
        return
    now = captured_at or utcnow()
    value = int(rr or 0)
    latest = _latest_rank(db)
    if (
        latest is not None
        and _aware(latest.captured_at)
        and _aware(latest.captured_at).date() == now.date()
    ):
        latest.rank_name = profile.rank_name
        latest.rank_tier = profile.rank_tier
        latest.rr = value
        latest.last_change = last_change
        latest.source = source
        return
    db.add(
        RankSnapshot(
            rank_name=profile.rank_name,
            rank_tier=profile.rank_tier,
            rr=value,
            last_change=last_change,
            source=source,
            captured_at=now,
        )
    )


def _seed_demo_rank_history(db: Session, profile: Profile) -> None:
    """En demo no hay MMR real: generamos una progresion determinista."""
    if db.scalar(select(RankSnapshot.id).limit(1)) is not None:
        return
    now = utcnow()
    progression = [8, 21, 15, 34, 29, 47, 39, 42]
    changes = [12, 13, -6, 19, -5, 18, -8, 3]
    for index, (rr, change) in enumerate(zip(progression, changes)):
        db.add(
            RankSnapshot(
                rank_name=profile.rank_name,
                rank_tier=profile.rank_tier,
                rr=rr,
                last_change=change,
                source="demo",
                captured_at=now - timedelta(days=len(progression) - 1 - index),
            )
        )


async def sync_matches(db: Session, profile: Profile) -> dict:
    provider = build_provider(profile, settings.demo_match_count)

    if profile.provider == "henrik":
        account = await provider.fetch_account(profile)
        if account.puuid:
            profile.puuid = account.puuid
        profile.riot_id = account.name
        profile.tag = account.tag
        profile.region = account.region
        try:
            rank = await provider.fetch_rank(profile)
            _apply_rank(profile, rank)
            rr = rank.rank_rr
            last_change = rank.rank_last_change
        except ProviderError:
            # El rango es opcional: si Henrik no responde, las partidas siguen
            # sincronizandose y el rango queda como estaba.
            rr = None
            last_change = None
        matches = await provider.fetch_matches(profile)
    else:
        account = provider.fetch_account(profile)
        profile.puuid = account.puuid
        _apply_rank(profile, account)
        rr = account.rank_rr
        last_change = account.rank_last_change
        _seed_demo_rank_history(db, profile)
        matches = provider.fetch_matches(profile)

    added = 0
    skipped = 0
    for data in matches:
        if not data.match_id or db.get(Match, data.match_id) is not None:
            skipped += 1
            continue
        _persist_match(db, data)
        added += 1

    if rr is not None or profile.rank_name:
        _record_rank(db, profile, rr, last_change, profile.provider)

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


def _ensure_metric_extras(metrics: dict, rounds: list[dict]) -> dict:
    if "buy_rounds" in metrics and "key_rounds" in metrics:
        return metrics
    from .analysis.metrics import _economy_stats, _key_rounds

    parsed = _rounds_from_json(rounds)
    extras = _economy_stats(parsed)
    extras["key_rounds"] = _key_rounds(parsed)
    extras.setdefault("clutch_attempts", 0)
    extras.setdefault("clutch_wins", 0)
    extras.setdefault("clutch_rate", 0.0)
    extras.setdefault("clutch_kills", 0)
    return {**extras, **metrics}


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
    metrics = _ensure_metric_extras(match.metrics or {}, match.rounds or [])
    return {
        **match_summary(match),
        "metrics": metrics,
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


def _avg(items: list[Match], key: str) -> float:
    if not items:
        return 0.0
    values = [getattr(item, key) or 0 for item in items]
    return round(sum(values) / len(values), 1)


def _metric_avg(matches: list[Match], key: str) -> float:
    if not matches:
        return 0.0
    values = [float((match.metrics or {}).get(key, 0) or 0) for match in matches]
    return round(sum(values) / len(values), 1)


def _group_breakdown(matches: list[Match], key: str) -> list[dict]:
    groups: dict[str, list[Match]] = {}
    for match in matches:
        value = (getattr(match, key) or "Desconocido").strip() or "Desconocido"
        groups.setdefault(value, []).append(match)
    rows = []
    for name, items in groups.items():
        wins = sum(1 for item in items if item.result == "win")
        rows.append(
            {
                "name": name,
                "matches": len(items),
                "wins": wins,
                "losses": len(items) - wins,
                "winrate": round(wins / len(items) * 100, 1),
                "acs": _avg(items, "acs"),
                "adr": _avg(items, "adr"),
                "kast": _avg(items, "kast"),
                "hs_pct": _avg(items, "hs_pct"),
            }
        )
    rows.sort(key=lambda row: (row["matches"], row["winrate"]), reverse=True)
    return rows


def _economy_overview(matches: list[Match]) -> dict:
    rounds = {key: 0 for key in ("full", "force", "save", "unknown")}
    wins = {key: 0 for key in rounds}
    loadouts: list[float] = []
    for match in matches:
        metrics = match.metrics or {}
        for key, value in (metrics.get("buy_rounds") or {}).items():
            if key in rounds:
                rounds[key] += int(value or 0)
        for key, value in (metrics.get("buy_wins") or {}).items():
            if key in wins:
                wins[key] += int(value or 0)
        if metrics.get("avg_loadout") is not None:
            loadouts.append(float(metrics["avg_loadout"]))
    winrate = {
        key: round(wins[key] / rounds[key] * 100, 1) if rounds[key] else 0.0
        for key in rounds
    }
    return {
        "rounds": rounds,
        "wins": wins,
        "winrate": winrate,
        "avg_loadout": round(sum(loadouts) / len(loadouts), 0) if loadouts else 0,
        "score": _metric_avg(matches, "econ_score"),
    }


def _clutch_overview(matches: list[Match]) -> dict:
    attempts = sum(
        int((match.metrics or {}).get("clutch_attempts", 0) or 0) for match in matches
    )
    wins = sum(int((match.metrics or {}).get("clutch_wins", 0) or 0) for match in matches)
    kills = sum(
        int((match.metrics or {}).get("clutch_kills", 0) or 0) for match in matches
    )
    return {
        "attempts": attempts,
        "wins": wins,
        "kills": kills,
        "rate": round(wins / attempts * 100, 1) if attempts else 0.0,
    }


def _rank_overview(db: Session) -> dict:
    snapshots = list(
        db.scalars(
            select(RankSnapshot).order_by(RankSnapshot.captured_at.asc())
        ).all()
    )[-30:]
    if not snapshots:
        return {"current": None, "history": [], "delta": 0}
    history = [
        {
            "date": _iso(snapshot.captured_at),
            "rr": snapshot.rr,
            "rank_name": snapshot.rank_name,
            "rank_tier": snapshot.rank_tier,
            "last_change": snapshot.last_change,
        }
        for snapshot in snapshots
    ]
    current = history[-1]
    delta = current["rr"] - history[0]["rr"]
    tier_delta = (current["rank_tier"] or 0) - (history[0]["rank_tier"] or 0)
    if tier_delta:
        delta = tier_delta * 100 + delta
    return {"current": current, "history": history, "delta": delta}


def _filter_matches(
    matches: list[Match], mode: str | None, days: int | None
) -> list[Match]:
    filtered = matches
    if days:
        cutoff = utcnow() - timedelta(days=days)
        filtered = [
            match
            for match in filtered
            if _aware(match.started_at) and _aware(match.started_at) >= cutoff
        ]
    if mode and mode != "all":
        wanted = normalize_mode(mode)
        filtered = [
            match
            for match in filtered
            if normalize_mode(match.mode) == wanted
            or normalize_mode(match.queue) == wanted
        ]
    return filtered


def build_overview(
    db: Session, mode: str | None = None, days: int | None = None
) -> dict:
    profile = get_or_create_profile(db)
    all_matches = list(
        db.scalars(select(Match).order_by(Match.started_at.desc())).all()
    )
    matches = _filter_matches(all_matches, mode, days)

    wins = sum(1 for m in matches if m.result == "win")
    losses = sum(1 for m in matches if m.result == "loss")
    total = len(matches)
    kills = sum(m.kills for m in matches)
    deaths = sum(m.deaths for m in matches)
    assists = sum(m.assists for m in matches)

    def avg(key: str) -> float:
        return _avg(matches, key)

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

    avg_metrics = {
        "acs": avg("acs"),
        "adr": avg("adr"),
        "hs_pct": avg("hs_pct"),
        "kast": avg("kast"),
        "fb_rate": _metric_avg(matches, "fb_rate"),
    }

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
        "filters": {
            "mode": normalize_mode(mode) if mode and mode != "all" else None,
            "days": days,
            "total_matches": len(all_matches),
            "filtered_matches": total,
        },
        "rank": _rank_overview(db),
        "benchmarks": build_benchmarks(avg_metrics, profile.rank_name, profile.rank_tier),
        "breakdowns": {
            "maps": _group_breakdown(matches, "map_name"),
            "agents": _group_breakdown(matches, "agent"),
        },
        "economy": _economy_overview(matches),
        "clutches": _clutch_overview(matches),
        "goals": goals_list(db),
        "top_patterns": top_patterns,
        "strengths": top_strengths,
        "trend": trend,
        "recent": [match_summary(m) for m in matches[:6]],
    }


def list_matches(
    db: Session,
    limit: int = 100,
    mode: str | None = None,
    days: int | None = None,
) -> list[dict]:
    matches = list(
        db.scalars(select(Match).order_by(Match.started_at.desc())).all()
    )
    matches = _filter_matches(matches, mode, days)
    return [match_summary(m) for m in matches[: min(limit, 200)]]


def reset_matches(db: Session, *, include_goals: bool = False) -> None:
    db.execute(delete(Insight))
    db.execute(delete(Report))
    db.execute(delete(Match))
    db.execute(delete(RankSnapshot))
    if include_goals:
        db.execute(delete(Goal))
    db.commit()


def reset_data(db: Session) -> None:
    reset_matches(db, include_goals=True)


def goals_list(db: Session) -> list[dict]:
    goals = db.scalars(select(Goal).order_by(Goal.status, Goal.created_at.desc())).all()
    return [
        {
            "id": goal.id,
            "title": goal.title,
            "detail": goal.detail,
            "rule_id": goal.rule_id,
            "status": goal.status,
            "target": goal.target,
            "created_at": _iso(goal.created_at),
            "completed_at": _iso(goal.completed_at),
        }
        for goal in goals
    ]


def goal_create(
    db: Session, title: str, detail: str = "", rule_id: str | None = None,
    target: str = "",
) -> dict:
    goal = Goal(
        title=title.strip()[:160],
        detail=detail.strip(),
        rule_id=rule_id,
        target=target.strip(),
    )
    db.add(goal)
    db.commit()
    db.refresh(goal)
    return next(item for item in goals_list(db) if item["id"] == goal.id)


def goal_update(db: Session, goal_id: int, status: str | None = None) -> dict | None:
    goal = db.get(Goal, goal_id)
    if goal is None:
        return None
    if status in ("active", "done"):
        goal.status = status
        goal.completed_at = utcnow() if status == "done" else None
    db.commit()
    db.refresh(goal)
    return next(item for item in goals_list(db) if item["id"] == goal.id)


def goal_delete(db: Session, goal_id: int) -> bool:
    goal = db.get(Goal, goal_id)
    if goal is None:
        return False
    db.delete(goal)
    db.commit()
    return True


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
