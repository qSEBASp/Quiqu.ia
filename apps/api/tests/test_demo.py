from app.analysis.metrics import compute_metrics
from app.analysis.report import build_report
from app.analysis.rules import evaluate
from app.models import Profile
from app.providers.demo import DemoProvider


def profile() -> Profile:
    return Profile(id=1, riot_id="Tester", tag="EUW", region="eu", provider="demo")


def test_demo_generates_consistent_matches():
    matches = DemoProvider(14).fetch_matches(profile())
    assert len(matches) == 14
    assert len({m.match_id for m in matches}) == 14

    for match in matches:
        assert match.rounds, "cada partida debe tener rondas"
        assert max(match.score_us, match.score_them) == 13
        assert match.result == ("win" if match.score_us > match.score_them else "loss")
        assert match.overall.kills == sum(r.kills for r in match.rounds)
        assert match.overall.deaths == sum(r.deaths for r in match.rounds)
        assert len(match.scoreboard) == 10
        assert sum(1 for p in match.scoreboard if p.is_me) == 1

        metrics = compute_metrics(match)
        assert 0 <= metrics["kast"] <= 100
        assert 0 <= metrics["hs_pct"] <= 100
        assert metrics["acs"] > 0
        assert metrics["adr"] > 0

        findings = evaluate(match, metrics)
        report = build_report(match, metrics, findings)
        assert report["summary"]
        assert report["model"] == "rules"
        for finding in findings:
            assert finding.recommendation
            assert finding.detail
            assert 1 <= finding.severity <= 5


def test_demo_produces_actionable_insights():
    matches = DemoProvider(14).fetch_matches(profile())
    all_findings = []
    for match in matches:
        metrics = compute_metrics(match)
        all_findings.extend(evaluate(match, metrics))

    rule_ids = {f.rule_id for f in all_findings}
    assert len(all_findings) >= 5
    assert "force_buy_after_loss" in rule_ids or "attack_no_utility" in rule_ids


def test_demo_is_deterministic():
    first = DemoProvider(3).fetch_matches(profile())
    second = DemoProvider(3).fetch_matches(profile())
    for a, b in zip(first, second):
        assert a.match_id == b.match_id
        assert a.score_us == b.score_us
        assert a.overall.kills == b.overall.kills
        assert [r.kills for r in a.rounds] == [r.kills for r in b.rounds]
