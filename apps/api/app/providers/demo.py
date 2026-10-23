import hashlib
import random
from datetime import datetime, timedelta, timezone

from ..constants import AGENTS, DEMO_PLAYERS, MAPS, RANKS
from ..models import Profile
from .base import (
    AccountData,
    KillEvent,
    MatchData,
    OverallStats,
    RoundData,
    ScoreboardEntry,
)

STYLES = {
    "disciplined": {
        "win_bonus": 0.07,
        "first_death": 0.11,
        "first_blood": 0.17,
        "trade": 0.48,
        "util": 1.0,
        "force": 0.25,
        "no_armor": 0.03,
        "hs": 0.27,
        "impact": 1.0,
    },
    "aggressive": {
        "win_bonus": 0.02,
        "first_death": 0.24,
        "first_blood": 0.24,
        "trade": 0.32,
        "util": 0.85,
        "force": 0.5,
        "no_armor": 0.1,
        "hs": 0.3,
        "impact": 1.15,
    },
    "eco_chaos": {
        "win_bonus": -0.05,
        "first_death": 0.2,
        "first_blood": 0.15,
        "trade": 0.3,
        "util": 0.55,
        "force": 0.85,
        "no_armor": 0.24,
        "hs": 0.23,
        "impact": 1.0,
    },
    "passive": {
        "win_bonus": -0.03,
        "first_death": 0.08,
        "first_blood": 0.09,
        "trade": 0.4,
        "util": 0.9,
        "force": 0.3,
        "no_armor": 0.05,
        "hs": 0.22,
        "impact": 0.78,
    },
    "inconsistent": {
        "win_bonus": 0.0,
        "first_death": 0.18,
        "first_blood": 0.18,
        "trade": 0.36,
        "util": 0.8,
        "force": 0.55,
        "no_armor": 0.14,
        "hs": 0.25,
        "impact": 1.0,
    },
}

STYLE_ORDER = ["disciplined", "aggressive", "eco_chaos", "passive", "inconsistent"]


def _seed(value: str) -> int:
    return int(hashlib.sha256(value.encode("utf-8")).hexdigest()[:12], 16)


def _buy_type(credits: int, force_bias: float, rng: random.Random) -> str:
    if credits >= 3900:
        return "full"
    if credits >= 2500 and rng.random() < 0.25 + force_bias * 0.35:
        return "force"
    if credits >= 1800 and rng.random() < force_bias * 0.35:
        return "force"
    return "save"


def _spend_for(buy: str, credits: int, rng: random.Random) -> int:
    if buy == "full":
        return min(credits, rng.randint(3900, 4700))
    if buy == "force":
        return min(credits, rng.randint(1800, 3100))
    return min(credits, rng.randint(0, 600))


class DemoProvider:
    def __init__(self, count: int = 14):
        self.count = max(1, count)

    def fetch_account(self, profile: Profile) -> AccountData:
        return AccountData(
            puuid=f"demo-{profile.riot_id.lower()}",
            name=profile.riot_id,
            tag=profile.tag,
            region=profile.region,
            platform=profile.platform,
            rank_name="Diamante 2",
            rank_tier=17,
            rank_rr=42,
            rank_last_change=18,
        )

    def fetch_matches(self, profile: Profile) -> list[MatchData]:
        return [
            self._generate_match(profile, index)
            for index in range(self.count)
        ]

    def _generate_match(self, profile: Profile, index: int) -> MatchData:
        rng = random.Random(_seed(f"{profile.riot_id}#{profile.tag}:{index}"))
        style_name = STYLE_ORDER[index % len(STYLE_ORDER)]
        style = STYLES[style_name]
        agent, role = AGENTS[(index * 3 + 1) % len(AGENTS)]
        map_name = MAPS[(index * 3 + 2) % len(MAPS)]
        start_side = "attack" if index % 2 == 0 else "defense"

        score_us = 0
        score_them = 0
        credits = 800
        rounds: list[RoundData] = []
        number = 0
        side = start_side

        while score_us < 13 and score_them < 13 and number < 30:
            number += 1
            if number == 13:
                side = "defense" if start_side == "attack" else "attack"

            attack_penalty = -0.03 if side == "attack" else 0.015
            win_chance = 0.5 + style["win_bonus"] + attack_penalty + rng.uniform(-0.06, 0.06)
            won = rng.random() < win_chance

            buy = _buy_type(credits, style["force"], rng)
            spent = _spend_for(buy, credits, rng)
            remaining = max(0, credits - spent)
            loadout = spent if buy != "save" else min(spent + 200, credits)
            if buy == "full":
                has_armor = True
            elif buy == "force":
                has_armor = rng.random() >= style["no_armor"]
            else:
                has_armor = rng.random() < 0.15

            died = rng.random() < (0.6 if won else 0.78)
            first_death = died and rng.random() < style["first_death"] * 1.6
            first_blood = (not first_death) and rng.random() < style["first_blood"]

            if won:
                kills = rng.choices([0, 1, 2, 3], weights=[0.3, 0.48, 0.18, 0.04])[0]
            else:
                kills = rng.choices([0, 1, 2, 3], weights=[0.45, 0.42, 0.11, 0.02])[0]
            if first_blood:
                kills = max(1, kills)
            if first_death:
                kills = max(0, kills - 1)

            deaths = 1 if died else 0
            assists = rng.choices([0, 1, 2], weights=[0.52, 0.38, 0.1])[0]
            damage = int(
                (60 + kills * 58 + rng.randint(0, 70))
                * style["impact"]
                * (1.08 if won else 0.92)
            )
            damage = max(0, min(320, damage))

            shots = rng.randint(6, 16) + kills * 3
            headshots = int(shots * (style["hs"] + rng.uniform(-0.04, 0.05)))
            headshots = max(0, min(shots, headshots))
            legshots = rng.randint(0, 2)
            bodyshots = max(0, shots - headshots - legshots)

            abilities = rng.randint(1, 4) if role in ("Controlador", "Iniciador", "Centinela") else rng.randint(1, 3)
            abilities = int(round(abilities * style["util"] + rng.uniform(-0.4, 0.4)))
            if side == "attack" and rng.random() < 0.16:
                abilities = 0
            abilities = max(0, min(5, abilities))
            ult_used = rng.random() < 0.16

            if died:
                traded = rng.random() < style["trade"]
            else:
                traded = False

            weapon = None
            if buy == "full":
                weapon = rng.choice(["Vandal", "Phantom", "Operator", "Phantom"])
            elif buy == "force":
                weapon = rng.choice(["Spectre", "Marshal", "Guardian", "Spectre"])
            elif loadout > 0:
                weapon = rng.choice(["Classic", "Sheriff", "Ghost"])

            round_score = int(kills * 120 + assists * 30 + damage * 0.5 + (20 if won else 0))

            reason = "Elimination"
            if won and side == "attack" and rng.random() < 0.5:
                reason = "Spike detonated"
            elif won and side == "defense" and rng.random() < 0.35:
                reason = "Spike defused"
            elif not won and rng.random() < 0.07:
                reason = "Time expired"

            rounds.append(
                RoundData(
                    number=number,
                    side=side,
                    won=won,
                    reason=reason,
                    kills=kills,
                    deaths=deaths,
                    assists=assists,
                    survived=not died,
                    damage=damage,
                    headshots=headshots,
                    bodyshots=bodyshots,
                    legshots=legshots,
                    first_blood=first_blood,
                    first_death=first_death,
                    traded_death=traded,
                    loadout_value=loadout,
                    credits_remaining=remaining,
                    abilities_used=abilities,
                    ult_used=ult_used,
                    has_armor=has_armor,
                    weapon=weapon,
                    buy_type=buy,
                )
            )

            if won:
                score_us += 1
            else:
                score_them += 1

            credits = min(9000, remaining + (3000 if won else 1900) + kills * 200)

        kills_total = sum(r.kills for r in rounds)
        deaths_total = sum(r.deaths for r in rounds)
        assists_total = sum(r.assists for r in rounds)
        score_total = sum(
            int(r.kills * 120 + r.assists * 30 + r.damage * 0.5 + (20 if r.won else 0))
            for r in rounds
        )
        overall = OverallStats(
            kills=kills_total,
            deaths=deaths_total,
            assists=assists_total,
            score=score_total,
            damage_dealt=sum(r.damage for r in rounds),
            headshots=sum(r.headshots for r in rounds),
            bodyshots=sum(r.bodyshots for r in rounds),
            legshots=sum(r.legshots for r in rounds),
        )

        started_at = datetime.now(timezone.utc) - timedelta(
            days=index, hours=6 + (index % 5), minutes=rng.randint(0, 59)
        )
        duration = int(24 + len(rounds) * 1.6)

        scoreboard = self._scoreboard(rng, index, profile, agent, overall, len(rounds))

        return MatchData(
            match_id=f"demo-{index + 1:02d}",
            started_at=started_at,
            map_name=map_name,
            mode="Competitivo",
            queue="competitive",
            agent=agent,
            agent_role=role,
            result="win" if score_us > score_them else "loss",
            score_us=score_us,
            score_them=score_them,
            duration_min=duration,
            name=profile.riot_id,
            tag=profile.tag,
            puuid=f"demo-{profile.riot_id.lower()}",
            team_id="Blue",
            overall=overall,
            rounds=rounds,
            scoreboard=scoreboard,
        )

    def _scoreboard(
        self,
        rng: random.Random,
        index: int,
        profile: Profile,
        agent: str,
        overall: OverallStats,
        round_count: int,
    ) -> list[ScoreboardEntry]:
        entries: list[ScoreboardEntry] = []
        names = DEMO_PLAYERS[index % len(DEMO_PLAYERS):] + DEMO_PLAYERS[: index % len(DEMO_PLAYERS)]
        used_agents = [agent]

        for i, name in enumerate(names[:4]):
            other_agent, _ = AGENTS[(index + i * 2) % len(AGENTS)]
            used_agents.append(other_agent)
            k = max(2, int(overall.kills * rng.uniform(0.5, 1.1)))
            d = max(2, int(round_count * rng.uniform(0.55, 0.85)))
            a = rng.randint(1, 6)
            entries.append(
                ScoreboardEntry(
                    name=name,
                    tag=str(rng.randint(1000, 9999)),
                    team="Blue",
                    agent=other_agent,
                    kills=k,
                    deaths=d,
                    assists=a,
                    acs=round(rng.uniform(150, 300), 1),
                )
            )

        for i, name in enumerate(names[4:9]):
            other_agent, _ = AGENTS[(index + 3 + i * 2) % len(AGENTS)]
            k = max(2, int(overall.kills * rng.uniform(0.6, 1.15)))
            d = max(2, int(round_count * rng.uniform(0.55, 0.85)))
            a = rng.randint(1, 6)
            entries.append(
                ScoreboardEntry(
                    name=name,
                    tag=str(rng.randint(1000, 9999)),
                    team="Red",
                    agent=other_agent,
                    kills=k,
                    deaths=d,
                    assists=a,
                    acs=round(rng.uniform(150, 300), 1),
                )
            )

        entries.append(
            ScoreboardEntry(
                name=profile.riot_id,
                tag=profile.tag,
                team="Blue",
                agent=agent,
                kills=overall.kills,
                deaths=overall.deaths,
                assists=overall.assists,
                acs=round(overall.score / max(1, round_count), 1),
                is_me=True,
            )
        )
        return entries
