from datetime import datetime, timezone
from typing import Any

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Profile(Base):
    __tablename__ = "profile"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    riot_id: Mapped[str] = mapped_column(String(64), default="qSEBA")
    tag: Mapped[str] = mapped_column(String(16), default="EUW")
    region: Mapped[str] = mapped_column(String(16), default="eu")
    platform: Mapped[str] = mapped_column(String(16), default="pc")
    puuid: Mapped[str | None] = mapped_column(String(128), nullable=True)
    rank_name: Mapped[str | None] = mapped_column(String(64), nullable=True)
    rank_tier: Mapped[int | None] = mapped_column(Integer, nullable=True)
    provider: Mapped[str] = mapped_column(String(16), default="demo")
    henrik_api_key: Mapped[str] = mapped_column(String(256), default="")
    onboarded: Mapped[bool] = mapped_column(Boolean, default=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Match(Base):
    __tablename__ = "matches"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    map_name: Mapped[str] = mapped_column(String(32))
    mode: Mapped[str] = mapped_column(String(32), default="Competitivo")
    queue: Mapped[str] = mapped_column(String(32), default="competitive")
    agent: Mapped[str] = mapped_column(String(32))
    agent_role: Mapped[str] = mapped_column(String(32), default="")
    result: Mapped[str] = mapped_column(String(8), default="win")
    score_us: Mapped[int] = mapped_column(Integer, default=0)
    score_them: Mapped[int] = mapped_column(Integer, default=0)
    kills: Mapped[int] = mapped_column(Integer, default=0)
    deaths: Mapped[int] = mapped_column(Integer, default=0)
    assists: Mapped[int] = mapped_column(Integer, default=0)
    acs: Mapped[float] = mapped_column(Float, default=0)
    adr: Mapped[float] = mapped_column(Float, default=0)
    hs_pct: Mapped[float] = mapped_column(Float, default=0)
    kast: Mapped[float] = mapped_column(Float, default=0)
    first_bloods: Mapped[int] = mapped_column(Integer, default=0)
    first_deaths: Mapped[int] = mapped_column(Integer, default=0)
    trade_rate: Mapped[float] = mapped_column(Float, default=0)
    econ_score: Mapped[float] = mapped_column(Float, default=0)
    util_usage: Mapped[float] = mapped_column(Float, default=0)
    scoreboard: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    metrics: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    rounds: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    raw: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    source: Mapped[str] = mapped_column(String(16), default="demo")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    insights: Mapped[list["Insight"]] = relationship(
        back_populates="match", cascade="all, delete-orphan", lazy="selectin"
    )
    report: Mapped["Report | None"] = relationship(
        back_populates="match", cascade="all, delete-orphan", uselist=False, lazy="selectin"
    )


class Insight(Base):
    __tablename__ = "insights"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    match_id: Mapped[str] = mapped_column(ForeignKey("matches.id", ondelete="CASCADE"), index=True)
    rule_id: Mapped[str] = mapped_column(String(64), index=True)
    category: Mapped[str] = mapped_column(String(32))
    severity: Mapped[int] = mapped_column(Integer, default=1)
    title: Mapped[str] = mapped_column(String(160))
    detail: Mapped[str] = mapped_column(Text)
    recommendation: Mapped[str] = mapped_column(Text, default="")
    evidence: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    metric: Mapped[float | None] = mapped_column(Float, nullable=True)
    threshold: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    match: Mapped[Match] = relationship(back_populates="insights")


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    match_id: Mapped[str] = mapped_column(
        ForeignKey("matches.id", ondelete="CASCADE"), unique=True, index=True
    )
    summary: Mapped[str] = mapped_column(Text)
    priorities: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    drills: Mapped[list[str]] = mapped_column(JSON, default=list)
    model: Mapped[str] = mapped_column(String(64), default="rules")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    match: Mapped[Match] = relationship(back_populates="report")
