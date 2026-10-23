import logging
from datetime import datetime, timezone
from urllib.parse import quote

import httpx

from ..constants import AGENT_ROLES
from ..models import Profile
from .base import (
    AccountData,
    KillEvent,
    MatchData,
    OverallStats,
    ProviderError,
    RoundData,
    ScoreboardEntry,
)

logger = logging.getLogger(__name__)

ROUND_BASED_MODES = {
    "competitive",
    "unrated",
    "swiftplay",
    "spike rush",
    "spikerush",
    "premier",
}


class HenrikProvider:
    def __init__(self, api_key: str, base_url: str = "https://api.henrikdev.xyz"):
        self.api_key = api_key.strip()
        self.base_url = base_url.rstrip("/")

    async def _get(self, path: str, params: dict | None = None):
        if not self.api_key:
            raise ProviderError(
                "Falta la API key de HenrikDev. Configúrala en Ajustes o usa el modo demo."
            )
        headers = {"Authorization": self.api_key, "Accept": "application/json"}
        async with httpx.AsyncClient(timeout=30) as client:
            try:
                response = await client.get(
                    f"{self.base_url}{path}", headers=headers, params=params
                )
            except httpx.HTTPError as exc:
                logger.warning("No se pudo conectar con HenrikDev: %s", exc)
                raise ProviderError(
                    "No se pudo conectar con HenrikDev. Revisa tu conexión."
                ) from exc
        if response.status_code in (401, 403):
            raise ProviderError("La API key de HenrikDev no es válida o no tiene permisos.")
        if response.status_code == 429:
            raise ProviderError("Límite de peticiones de HenrikDev alcanzado. Espera un momento.")
        if response.status_code >= 400:
            logger.warning(
                "HenrikDev respondió %s: %s",
                response.status_code,
                response.text[:500],
            )
            raise ProviderError(
                f"HenrikDev respondió con un error ({response.status_code}). "
                "Inténtalo más tarde."
            )
        payload = response.json()
        if payload.get("errors"):
            logger.warning("HenrikDev devolvió errores: %s", payload["errors"])
            raise ProviderError("HenrikDev devolvió un error inesperado.")
        return payload.get("data")

    async def fetch_account(self, profile: Profile) -> AccountData:
        name = quote(profile.riot_id, safe="")
        tag = quote(profile.tag, safe="")
        data = await self._get(f"/valorant/v1/account/{name}/{tag}")
        if not data:
            raise ProviderError("No se encontró esa cuenta de Riot.")
        return AccountData(
            puuid=data.get("puuid"),
            name=data.get("name") or profile.riot_id,
            tag=data.get("tag") or profile.tag,
            region=(data.get("region") or profile.region).lower(),
            platform=profile.platform,
        )

    async def fetch_rank(self, profile: Profile) -> AccountData:
        puuid = profile.puuid
        if not puuid:
            account = await self.fetch_account(profile)
            puuid = account.puuid
        if not puuid:
            raise ProviderError("No se pudo resolver el PUUID para consultar el rango.")

        data = await self._get(
            f"/valorant/v3/by-puuid/mmr/{profile.region}/{profile.platform}/"
            f"{quote(puuid, safe='')}"
        )
        if not isinstance(data, dict):
            raise ProviderError("Respuesta inesperada al consultar el rango.")
        current = data.get("current") or {}
        tier = current.get("tier") or {}
        return AccountData(
            puuid=puuid,
            name=profile.riot_id,
            tag=profile.tag,
            region=profile.region,
            platform=profile.platform,
            rank_name=tier.get("name"),
            rank_tier=tier.get("id"),
            rank_rr=current.get("rr"),
            rank_last_change=current.get("last_change"),
        )

    async def fetch_matches(self, profile: Profile, puuid: str | None = None) -> list[MatchData]:
        puuid = puuid or profile.puuid
        if not puuid:
            account = await self.fetch_account(profile)
            puuid = account.puuid
        if not puuid:
            raise ProviderError("No se pudo resolver el PUUID de la cuenta.")

        data = await self._get(
            f"/valorant/v4/by-puuid/matches/{profile.region}/{profile.platform}/"
            f"{quote(puuid, safe='')}",
            params={"size": 10},
        )
        if not isinstance(data, list):
            raise ProviderError("Respuesta inesperada de HenrikDev.")
        matches: list[MatchData] = []
        for item in data:
            try:
                mapped = self._map_match(item, puuid, profile)
            except Exception:
                continue
            if not mapped or not mapped.rounds:
                continue
            if mapped.mode.strip().lower() not in ROUND_BASED_MODES:
                continue
            matches.append(mapped)
        return matches

    def _map_match(self, data: dict, puuid: str, profile: Profile) -> MatchData | None:
        meta = data.get("metadata") or {}
        players = data.get("players") or []
        teams = data.get("teams") or []
        me = next((p for p in players if p.get("puuid") == puuid), None)
        if not me:
            return None
        team_id = me.get("team_id")
        my_team = next((t for t in teams if t.get("team_id") == team_id), None)
        if not my_team:
            return None

        raw_rounds = data.get("rounds") or []
        round_count = len(raw_rounds)
        kills_by_round: dict[int, list[dict]] = {}
        for kill in data.get("kills") or []:
            kills_by_round.setdefault(int(kill.get("round", -1)), []).append(kill)

        inferred_sides = self._infer_sides(raw_rounds, team_id)
        rounds: list[RoundData] = []

        for index, raw in enumerate(raw_rounds):
            rid = int(raw.get("id", index))
            events = (
                kills_by_round.get(rid)
                or kills_by_round.get(index + 1)
                or kills_by_round.get(index)
                or []
            )
            events.sort(key=lambda k: k.get("time_in_round_in_ms") or 0)

            my_kills = 0
            my_deaths = 0
            my_assists = 0
            my_death_event = None
            for kill in events:
                killer = kill.get("killer") or {}
                victim = kill.get("victim") or {}
                assistants = kill.get("assistants") or []
                if killer.get("puuid") == puuid:
                    my_kills += 1
                if victim.get("puuid") == puuid:
                    my_deaths += 1
                    my_death_event = kill
                if any(a.get("puuid") == puuid for a in assistants):
                    my_assists += 1

            first_blood = (
                bool(events) and (events[0].get("killer") or {}).get("puuid") == puuid
            )
            first_death = bool(events) and (events[0].get("victim") or {}).get("puuid") == puuid
            traded = False
            if my_death_event:
                death_time = my_death_event.get("time_in_round_in_ms") or 0
                my_killer = (my_death_event.get("killer") or {}).get("puuid")
                for later in events:
                    if (later.get("time_in_round_in_ms") or 0) <= death_time:
                        continue
                    if (later.get("time_in_round_in_ms") or 0) - death_time > 5000:
                        break
                    later_victim = (later.get("victim") or {}).get("puuid")
                    later_killer = (later.get("killer") or {}).get("puuid")
                    if later_victim == my_killer and later_killer != puuid:
                        traded = True
                        break

            stats = next(
                (
                    s
                    for s in raw.get("stats") or []
                    if (s.get("player") or {}).get("puuid") == puuid
                ),
                None,
            )
            economy = (stats or {}).get("economy") or {}
            casts = (stats or {}).get("ability_casts") or {}
            my_round_stats = (stats or {}).get("stats") or {}
            damage = sum(
                int(e.get("damage") or 0) for e in (stats or {}).get("damage_events") or []
            )
            has_casts = any(value is not None for value in casts.values())
            abilities = (
                sum(int(casts.get(key) or 0) for key in ("ability_1", "ability_2", "grenade"))
                if has_casts
                else None
            )
            ult_used = int(casts.get("ultimate") or 0) > 0
            loadout = int(economy.get("loadout_value") or 0)
            buy_type = "full" if loadout >= 3500 else "force" if loadout >= 1800 else "save"

            rounds.append(
                RoundData(
                    number=index + 1,
                    side=inferred_sides.get(index, "unknown"),
                    won=raw.get("winning_team") == team_id,
                    reason=raw.get("result") or "Elimination",
                    kills=my_kills,
                    deaths=my_deaths,
                    assists=my_assists,
                    survived=my_deaths == 0,
                    damage=damage,
                    headshots=int(my_round_stats.get("headshots") or 0),
                    bodyshots=int(my_round_stats.get("bodyshots") or 0),
                    legshots=int(my_round_stats.get("legshots") or 0),
                    first_blood=first_blood,
                    first_death=first_death,
                    traded_death=traded,
                    loadout_value=loadout,
                    credits_remaining=int(economy.get("remaining") or 0),
                    abilities_used=abilities,
                    ult_used=ult_used,
                    has_armor=economy.get("armor") is not None,
                    weapon=((economy.get("weapon") or {}).get("name")),
                    buy_type=buy_type,
                )
            )

        stats = me.get("stats") or {}
        damage_dealt = ((stats.get("damage") or {}).get("dealt")) or 0
        overall = OverallStats(
            kills=int(stats.get("kills") or 0),
            deaths=int(stats.get("deaths") or 0),
            assists=int(stats.get("assists") or 0),
            score=int(stats.get("score") or 0),
            damage_dealt=int(damage_dealt),
            headshots=int(stats.get("headshots") or 0),
            bodyshots=int(stats.get("bodyshots") or 0),
            legshots=int(stats.get("legshots") or 0),
        )

        score_us = int(((my_team.get("rounds") or {}).get("won")) or 0)
        score_them = int(((my_team.get("rounds") or {}).get("lost")) or 0)
        agent = ((me.get("agent") or {}).get("name")) or "Desconocido"
        started_raw = meta.get("started_at") or ""
        try:
            started_at = datetime.fromisoformat(str(started_raw).replace("Z", "+00:00"))
        except ValueError:
            started_at = datetime.now(timezone.utc)
        if started_at.tzinfo is None:
            started_at = started_at.replace(tzinfo=timezone.utc)

        scoreboard = []
        for p in players:
            p_stats = p.get("stats") or {}
            scoreboard.append(
                ScoreboardEntry(
                    name=p.get("name") or "?",
                    tag=p.get("tag") or "",
                    team=p.get("team_id") or "",
                    agent=((p.get("agent") or {}).get("name")) or "?",
                    kills=int(p_stats.get("kills") or 0),
                    deaths=int(p_stats.get("deaths") or 0),
                    assists=int(p_stats.get("assists") or 0),
                    acs=round(int(p_stats.get("score") or 0) / max(1, round_count), 1),
                    is_me=p.get("puuid") == puuid,
                )
            )

        queue = meta.get("queue") or {}
        return MatchData(
            match_id=str(meta.get("match_id") or ""),
            started_at=started_at,
            map_name=((meta.get("map") or {}).get("name")) or "Desconocido",
            mode=queue.get("name") or "Competitivo",
            queue=queue.get("id") or "competitive",
            agent=agent,
            agent_role=AGENT_ROLES.get(agent, ""),
            result="win" if score_us > score_them else "loss" if score_them > score_us else "draw",
            score_us=score_us,
            score_them=score_them,
            duration_min=max(1, int((meta.get("game_length_in_ms") or 0) / 60000)),
            name=profile.riot_id,
            tag=profile.tag,
            puuid=puuid,
            team_id=team_id,
            overall=overall,
            rounds=rounds,
            kills=[
                KillEvent(
                    round=int(k.get("round", 0)),
                    time_ms=int(k.get("time_in_round_in_ms") or 0),
                    killer_puuid=(k.get("killer") or {}).get("puuid"),
                    victim_puuid=(k.get("victim") or {}).get("puuid"),
                    assistants=[
                        a.get("puuid") for a in (k.get("assistants") or []) if a.get("puuid")
                    ],
                    weapon=((k.get("weapon") or {}).get("name")),
                    killer_team=(k.get("killer") or {}).get("team"),
                    victim_team=(k.get("victim") or {}).get("team"),
                )
                for k in data.get("kills") or []
            ],
            scoreboard=scoreboard,
        )

    def _infer_sides(self, raw_rounds: list[dict], team_id: str) -> dict[int, str]:
        sides: dict[int, str | None] = {}
        for index, raw in enumerate(raw_rounds):
            side = None
            role = str(raw.get("winning_team_role") or "").lower()
            if role in ("attacker", "defender"):
                winning_side = "attack" if role == "attacker" else "defense"
                side = (
                    winning_side
                    if raw.get("winning_team") == team_id
                    else ("defense" if winning_side == "attack" else "attack")
                )

            if side is None:
                plant = raw.get("plant") or None
                defuse = raw.get("defuse") or None
                if plant and (plant.get("player") or {}).get("team"):
                    side = "attack" if plant["player"]["team"] == team_id else "defense"
                elif defuse and (defuse.get("player") or {}).get("team"):
                    side = "defense" if defuse["player"]["team"] == team_id else "attack"
            sides[index] = side

        for start, end in ((0, 12), (12, len(raw_rounds))):
            known = [sides[i] for i in range(start, min(end, len(raw_rounds))) if sides.get(i)]
            if not known:
                continue
            majority = max(set(known), key=known.count)
            for i in range(start, min(end, len(raw_rounds))):
                if sides.get(i) is None:
                    sides[i] = majority

        return {
            index: (side if side in ("attack", "defense") else "unknown")
            for index, side in sides.items()
        }
