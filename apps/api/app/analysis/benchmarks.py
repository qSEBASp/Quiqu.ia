import math

# Referencias orientativas por rango (no son datos oficiales de Riot). Sirven
# para dar contexto a una metrica: un ACS de 190 no significa lo mismo en
# Hierro que en Inmortal. Cada valor es la media esperada y la desviacion tipica
# aproximada de jugadores de ese rango.
BUCKETS: dict[str, dict] = {
    "iron": {
        "label": "Hierro",
        "acs": (140, 45),
        "adr": (105, 30),
        "kast": (58, 9),
        "hs_pct": (16, 7),
        "fb_rate": (8, 6),
    },
    "bronze": {
        "label": "Bronce",
        "acs": (155, 45),
        "adr": (115, 30),
        "kast": (61, 9),
        "hs_pct": (18, 7),
        "fb_rate": (9, 6),
    },
    "silver": {
        "label": "Plata",
        "acs": (170, 45),
        "adr": (125, 30),
        "kast": (64, 8),
        "hs_pct": (20, 7),
        "fb_rate": (10, 6),
    },
    "gold": {
        "label": "Oro",
        "acs": (185, 45),
        "adr": (135, 30),
        "kast": (67, 8),
        "hs_pct": (22, 7),
        "fb_rate": (11, 6),
    },
    "platinum": {
        "label": "Platino",
        "acs": (200, 45),
        "adr": (145, 30),
        "kast": (69, 8),
        "hs_pct": (23, 7),
        "fb_rate": (12, 6),
    },
    "diamond": {
        "label": "Diamante",
        "acs": (215, 45),
        "adr": (150, 30),
        "kast": (71, 7),
        "hs_pct": (24, 7),
        "fb_rate": (13, 6),
    },
    "ascendant": {
        "label": "Ascendente",
        "acs": (230, 45),
        "adr": (158, 30),
        "kast": (73, 7),
        "hs_pct": (25, 7),
        "fb_rate": (14, 6),
    },
    "immortal": {
        "label": "Inmortal",
        "acs": (245, 45),
        "adr": (165, 30),
        "kast": (75, 7),
        "hs_pct": (26, 7),
        "fb_rate": (15, 6),
    },
    "radiant": {
        "label": "Radiante",
        "acs": (260, 45),
        "adr": (175, 30),
        "kast": (77, 7),
        "hs_pct": (28, 7),
        "fb_rate": (16, 6),
    },
}

_NAME_TO_BUCKET = {
    "iron": "iron",
    "hierro": "iron",
    "bronze": "bronze",
    "bronce": "bronze",
    "silver": "silver",
    "plata": "silver",
    "gold": "gold",
    "oro": "gold",
    "platinum": "platinum",
    "platino": "platinum",
    "diamond": "diamond",
    "diamante": "diamond",
    "ascendant": "ascendant",
    "ascendente": "ascendant",
    "immortal": "immortal",
    "inmortal": "immortal",
    "radiant": "radiant",
    "radiante": "radiant",
}

METRICS = [
    ("acs", "ACS", ""),
    ("adr", "ADR", ""),
    ("kast", "KAST", "%"),
    ("hs_pct", "HS%", "%"),
    ("fb_rate", "Primeros contactos", "%"),
]


def rank_bucket(rank_name: str | None, rank_tier: int | None) -> str:
    if rank_name:
        lowered = rank_name.lower()
        for name, bucket in _NAME_TO_BUCKET.items():
            if name in lowered:
                return bucket
    # IDs de Riot: 3 = Hierro 1, 18 = Diamante 1, 27 = Radiante.
    if rank_tier and rank_tier >= 3:
        order = [
            "iron",
            "bronze",
            "silver",
            "gold",
            "platinum",
            "diamond",
            "ascendant",
            "immortal",
            "radiant",
        ]
        index = min(len(order) - 1, max(0, (rank_tier - 3) // 3))
        return order[index]
    return "gold"


def _percentile(value: float, mean: float, std: float) -> int:
    if std <= 0:
        return 50
    result = 0.5 * (1 + math.erf((value - mean) / (std * math.sqrt(2))))
    return max(1, min(99, round(result * 100)))


def build_benchmarks(
    metrics: dict, rank_name: str | None, rank_tier: int | None
) -> dict:
    bucket = rank_bucket(rank_name, rank_tier)
    reference = BUCKETS[bucket]
    items = []
    for key, label, unit in METRICS:
        value = float(metrics.get(key, 0) or 0)
        mean, std = reference[key]
        items.append(
            {
                "key": key,
                "label": label,
                "value": round(value, 1),
                "unit": unit,
                "baseline": mean,
                "percentile": _percentile(value, mean, std),
            }
        )
    best = max(items, key=lambda item: item["percentile"])
    worst = min(items, key=lambda item: item["percentile"])
    return {
        "bucket": bucket,
        "bucket_label": reference["label"],
        "items": items,
        "best": best["key"],
        "worst": worst["key"],
    }
