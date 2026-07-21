"""Race definitions used during character creation.

Each race is a plain dict so new races can be added without touching any
other code. stat_bonuses are added onto Player.BASE_STATS before class
bonuses are applied on top (see Player.create in entities.py).
"""

RACES = [
    {
        "name": "Human",
        "description": "Adaptable and balanced, unremarkable in any single way.",
        "stat_bonuses": {"CON": 1, "STR": 1, "DEX": 1, "INT": 1},
    },
    {
        "name": "Elf",
        "description": "Quick-witted and light on their feet, but physically frail.",
        "stat_bonuses": {"CON": 0, "STR": 0, "DEX": 1, "INT": 1},
    },
    {
        "name": "Dwarf",
        "description": "Stout and sturdy, built to take a beating.",
        "stat_bonuses": {"CON": 1, "STR": 1, "DEX": 0, "INT": 0},
    },
    {
        "name": "Orc",
        "description": "Brutish and powerful, with little patience for subtlety.",
        "stat_bonuses": {"CON": 0, "STR": 1, "DEX": 1, "INT": 0},
    },
    {
        "name": "Beastman",
        "description": "Small and nimble, relying on wit and speed to survive.",
        "stat_bonuses": {"CON": 1, "STR": 0, "DEX": 1, "INT": 0},
    },
    {
        "name": "Celestial",
        "description": "Small and nimble, relying on wit and speed to survive.",
        "stat_bonuses": {"CON": 1, "STR": 0, "DEX": 0, "INT": 1},
    },
    {
        "name": "Infernal",
        "description": "Small and nimble, relying on wit and speed to survive.",
        "stat_bonuses": {"CON": 0, "STR": 1, "DEX": 0, "INT": 1},
    },
]
