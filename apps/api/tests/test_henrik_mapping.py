from app.models import Profile
from app.providers.henrik import HenrikProvider


def player(puuid: str, team: str) -> dict:
    return {"puuid": puuid, "name": puuid, "tag": "EUW", "team": team}


def test_maps_v4_match_shape():
    me = "me-puuid"
    mate = "mate-puuid"
    enemy = "enemy-puuid"

    data = {
        "metadata": {
            "match_id": "abc-123",
            "map": {"id": "ascent", "name": "Ascent"},
            "started_at": "2026-10-20T18:00:00Z",
            "game_length_in_ms": 2_400_000,
            "queue": {"id": "competitive", "name": "Competitivo"},
        },
        "players": [
            {
                "puuid": me,
                "name": "Tester",
                "tag": "EUW",
                "team_id": "Blue",
                "agent": {"id": "jett", "name": "Jett"},
                "stats": {
                    "kills": 2,
                    "deaths": 1,
                    "assists": 1,
                    "score": 500,
                    "damage": {"dealt": 350, "received": 200},
                    "headshots": 5,
                    "bodyshots": 8,
                    "legshots": 1,
                },
            },
            {
                "puuid": mate,
                "name": "Mate",
                "tag": "EUW",
                "team_id": "Blue",
                "agent": {"name": "Omen"},
                "stats": {"kills": 1, "deaths": 1, "assists": 0, "score": 200},
            },
            {
                "puuid": enemy,
                "name": "Enemy",
                "tag": "EUW",
                "team_id": "Red",
                "agent": {"name": "Raze"},
                "stats": {"kills": 1, "deaths": 2, "assists": 0, "score": 200},
            },
        ],
        "teams": [
            {"team_id": "Blue", "won": True, "rounds": {"won": 2, "lost": 0}},
            {"team_id": "Red", "won": False, "rounds": {"won": 0, "lost": 2}},
        ],
        "rounds": [
            {
                "id": 0,
                "result": "Elimination",
                "winning_team": "Blue",
                "plant": {"player": player(me, "Blue"), "site": "A"},
                "defuse": None,
                "stats": [
                    {
                        "player": player(me, "Blue"),
                        "ability_casts": {
                            "ability_1": 1,
                            "ability_2": 1,
                            "grenade": 0,
                            "ultimate": 0,
                        },
                        "damage_events": [{"player": player(enemy, "Red"), "damage": 150}],
                        "stats": {"headshots": 3, "bodyshots": 4, "legshots": 0},
                        "economy": {
                            "loadout_value": 3900,
                            "remaining": 200,
                            "armor": {"id": "heavy"},
                            "weapon": {"name": "Vandal"},
                        },
                    }
                ],
            },
            {
                "id": 1,
                "result": "Elimination",
                "winning_team": "Blue",
                "plant": {"player": player(enemy, "Red"), "site": "B"},
                "defuse": None,
                "stats": [
                    {
                        "player": player(me, "Blue"),
                        "ability_casts": {
                            "ability_1": 0,
                            "ability_2": 1,
                            "grenade": 0,
                            "ultimate": 1,
                        },
                        "damage_events": [],
                        "stats": {"headshots": 0, "bodyshots": 2, "legshots": 0},
                        "economy": {
                            "loadout_value": 2000,
                            "remaining": 0,
                            "armor": None,
                            "weapon": {"name": "Spectre"},
                        },
                    }
                ],
            },
        ],
        "kills": [
            {
                "round": 0,
                "time_in_round_in_ms": 1000,
                "killer": player(me, "Blue"),
                "victim": player(enemy, "Red"),
                "assistants": [],
                "weapon": {"name": "Vandal"},
            },
            {
                "round": 1,
                "time_in_round_in_ms": 2000,
                "killer": player(enemy, "Red"),
                "victim": player(me, "Blue"),
                "assistants": [],
                "weapon": {"name": "Phantom"},
            },
            {
                "round": 1,
                "time_in_round_in_ms": 4000,
                "killer": player(mate, "Blue"),
                "victim": player(enemy, "Red"),
                "assistants": [player(me, "Blue")],
                "weapon": {"name": "Classic"},
            },
        ],
    }

    profile = Profile(id=1, riot_id="Tester", tag="EUW", region="eu", provider="henrik")
    mapped = HenrikProvider("key")._map_match(data, me, profile)

    assert mapped is not None
    assert mapped.map_name == "Ascent"
    assert mapped.score_us == 2
    assert mapped.result == "win"
    assert mapped.agent == "Jett"
    assert mapped.agent_role == "Duelista"
    assert len(mapped.rounds) == 2

    first, second = mapped.rounds
    assert first.side == "attack"
    assert first.first_blood is True
    assert first.first_death is False
    assert first.kills == 1
    assert first.weapon == "Vandal"
    assert first.has_armor is True
    assert first.buy_type == "full"
    assert first.abilities_used == 2

    assert second.side == "defense"
    assert second.first_death is True
    assert second.traded_death is True
    assert second.deaths == 1
    assert second.assists == 1
    assert second.has_armor is False
    assert second.buy_type == "force"
    assert second.ult_used is True

    assert len(mapped.scoreboard) == 3
    assert any(p.is_me for p in mapped.scoreboard)


def test_null_ability_casts_stay_unknown():
    me = "me-puuid"
    enemy = "enemy-puuid"

    data = {
        "metadata": {
            "match_id": "null-casts",
            "map": {"id": "ascent", "name": "Ascent"},
            "started_at": "2026-10-20T18:00:00Z",
            "game_length_in_ms": 1_800_000,
            "queue": {"id": "competitive", "name": "Competitivo"},
        },
        "players": [
            {
                "puuid": me,
                "name": "Tester",
                "tag": "EUW",
                "team_id": "Blue",
                "agent": {"name": "Omen"},
                "stats": {"kills": 0, "deaths": 1, "assists": 0, "score": 100},
            },
            {
                "puuid": enemy,
                "name": "Enemy",
                "tag": "EUW",
                "team_id": "Red",
                "agent": {"name": "Raze"},
                "stats": {"kills": 1, "deaths": 0, "assists": 0, "score": 200},
            },
        ],
        "teams": [
            {"team_id": "Blue", "rounds": {"won": 0, "lost": 1}},
            {"team_id": "Red", "rounds": {"won": 1, "lost": 0}},
        ],
        "rounds": [
            {
                "id": 0,
                "result": "Elimination",
                "winning_team": "Red",
                "plant": {"player": player(enemy, "Red"), "site": "A"},
                "defuse": None,
                "stats": [
                    {
                        "player": player(me, "Blue"),
                        "ability_casts": {
                            "ability_1": None,
                            "ability_2": None,
                            "grenade": None,
                            "ultimate": None,
                        },
                        "damage_events": [],
                        "stats": {"headshots": 0, "bodyshots": 0, "legshots": 0},
                        "economy": {
                            "loadout_value": 800,
                            "remaining": 0,
                            "armor": None,
                            "weapon": {"name": "Classic"},
                        },
                    }
                ],
            }
        ],
        "kills": [
            {
                "round": 0,
                "time_in_round_in_ms": 500,
                "killer": player(enemy, "Red"),
                "victim": player(me, "Blue"),
                "assistants": [],
                "weapon": {"name": "Classic"},
            }
        ],
    }

    profile = Profile(id=1, riot_id="Tester", tag="EUW", region="eu", provider="henrik")
    mapped = HenrikProvider("key")._map_match(data, me, profile)

    assert mapped is not None
    round_data = mapped.rounds[0]
    assert round_data.abilities_used is None
    assert round_data.first_death is True
    assert round_data.first_blood is False
    assert round_data.side == "defense"
