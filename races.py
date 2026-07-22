"""Race definitions used during character creation.

Each race is a plain dict so new races can be added without touching any
other code. stat_bonuses are added onto Player.BASE_STATS before class
bonuses are applied on top (see Player.create in entities.py).
"""

RACES = [
    {
        "name": "Human",
        "description": "An adaptable race. Capable of great good or evil.",
        "stat_bonuses": {"CON": 1, "STR": 1, "DEX": 1, "INT": 1},
    },
    {
        "name": "Elf",
        "description": "A high and imperious race. Noble and graceful.",
        "stat_bonuses": {"CON": 0, "STR": 0, "DEX": 1, "INT": 1},
    },
    {
        "name": "Dwarf",
        "description": "A sturdy and resilient race. Strong and enduring.",
        "stat_bonuses": {"CON": 1, "STR": 1, "DEX": 0, "INT": 0},
    },
    {
        "name": "Orc",
        "description": "A brutish and powerful race. Fierce and determined.",
        "stat_bonuses": {"CON": 0, "STR": 1, "DEX": 1, "INT": 0},
    },
    {
        "name": "Beastman",
        "description": "A wild and untamed race. They do what they must to survive.",
        "stat_bonuses": {"CON": 1, "STR": 0, "DEX": 1, "INT": 0},
    },
    {
        "name": "Celestial",
        "description": "A divine race. Their very aura inspires awe.",
        "stat_bonuses": {"CON": 1, "STR": 0, "DEX": 0, "INT": 1},
    },
    {
        "name": "Infernal",
        "description": "A demonic race. Their strength and cunning are unmatched.",
        "stat_bonuses": {"CON": 0, "STR": 1, "DEX": 0, "INT": 1},
    },
]
