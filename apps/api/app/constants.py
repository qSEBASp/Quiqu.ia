AGENTS: list[tuple[str, str]] = [
    ("Jett", "Duelista"),
    ("Raze", "Duelista"),
    ("Reyna", "Duelista"),
    ("Neon", "Duelista"),
    ("Iso", "Duelista"),
    ("Omen", "Controlador"),
    ("Brimstone", "Controlador"),
    ("Viper", "Controlador"),
    ("Astra", "Controlador"),
    ("Sova", "Iniciador"),
    ("Fade", "Iniciador"),
    ("KAY/O", "Iniciador"),
    ("Skye", "Iniciador"),
    ("Killjoy", "Centinela"),
    ("Cypher", "Centinela"),
    ("Chamber", "Centinela"),
    ("Deadlock", "Centinela"),
]

AGENT_ROLES: dict[str, str] = {name: role for name, role in AGENTS}

MAPS = [
    "Ascent",
    "Haven",
    "Split",
    "Bind",
    "Lotus",
    "Sunset",
    "Icebox",
    "Breeze",
    "Abyss",
    "Pearl",
]

DEMO_PLAYERS = [
    "Nova",
    "Kitsune",
    "Vex",
    "Drift",
    "Mako",
    "Zephyr",
    "Onyx",
    "Pixel",
    "Cinder",
    "Echo",
    "Rook",
    "Sable",
]

RANKS = [
    "Platino 1",
    "Platino 2",
    "Platino 3",
    "Diamante 1",
    "Diamante 2",
    "Diamante 3",
    "Ascendente 1",
]

REGIONS = ["eu", "na", "ap", "kr", "latam", "br"]
