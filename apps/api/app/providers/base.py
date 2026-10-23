from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

Side = Literal["attack", "defense", "unknown"]


class ProviderError(Exception):
    pass


class OverallStats(BaseModel):
    kills: int = 0
    deaths: int = 0
    assists: int = 0
    score: int = 0
    damage_dealt: int = 0
    headshots: int = 0
    bodyshots: int = 0
    legshots: int = 0


class RoundData(BaseModel):
    number: int
    side: Side = "unknown"
    won: bool = False
    reason: str = "Elimination"
    kills: int = 0
    deaths: int = 0
    assists: int = 0
    survived: bool = True
    damage: int = 0
    headshots: int = 0
    bodyshots: int = 0
    legshots: int = 0
    first_blood: bool = False
    first_death: bool = False
    traded_death: bool = False
    loadout_value: int = 0
    credits_remaining: int = 0
    abilities_used: int | None = None
    ult_used: bool = False
    has_armor: bool = True
    weapon: str | None = None
    buy_type: Literal["full", "force", "save", "unknown"] = "unknown"


class KillEvent(BaseModel):
    round: int
    time_ms: int = 0
    killer_puuid: str | None = None
    victim_puuid: str | None = None
    assistants: list[str] = Field(default_factory=list)
    weapon: str | None = None
    killer_team: str | None = None
    victim_team: str | None = None


class ScoreboardEntry(BaseModel):
    name: str
    tag: str = ""
    team: str
    agent: str
    kills: int = 0
    deaths: int = 0
    assists: int = 0
    acs: float = 0
    is_me: bool = False


class MatchData(BaseModel):
    match_id: str
    started_at: datetime
    map_name: str
    mode: str = "Competitivo"
    queue: str = "competitive"
    agent: str
    agent_role: str = ""
    result: Literal["win", "loss", "draw"] = "win"
    score_us: int = 0
    score_them: int = 0
    duration_min: int = 35
    name: str = ""
    tag: str = ""
    puuid: str | None = None
    team_id: str | None = None
    overall: OverallStats = Field(default_factory=OverallStats)
    rounds: list[RoundData] = Field(default_factory=list)
    kills: list[KillEvent] = Field(default_factory=list)
    scoreboard: list[ScoreboardEntry] = Field(default_factory=list)


class AccountData(BaseModel):
    puuid: str | None = None
    name: str
    tag: str
    region: str = "eu"
    platform: str = "pc"
    rank_name: str | None = None
    rank_tier: int | None = None
