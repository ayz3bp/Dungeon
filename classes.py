"""Class definitions used during character creation.

Stat bonuses stack with race bonuses in Player.create (see entities.py).
Starting gear is built from the same WEAPON_TEMPLATES / POTION_TEMPLATES
used by dungeon generation, so weapon/potion stats live in exactly one
place — a class just names which template it wants and gets a fixed
(non-random) mid-range roll of it.
"""

from generation import WEAPON_TEMPLATES, POTION_TEMPLATES
from items import Weapon, Potion


def _weapon(template_name):
    template = next(t for t in WEAPON_TEMPLATES if t["name"] == template_name)
    damage_min, damage_max = template["damage"]
    return Weapon(
        template["name"], template["description"], damage_min, damage_max,
        template.get("str_req", 0), template.get("attack_bonus", 0),
    )


def _potion(template_name):
    template = next(t for t in POTION_TEMPLATES if t["name"] == template_name)
    power = template["power"]
    if isinstance(power, tuple):
        low, high = power
        power = (low + high) // 2
    return Potion(template["name"], template["description"], template["kind"], power, template.get("duration", 0))


CLASSES = [
    {
        "name": "Warrior",
        "description": "A hardened front-line fighter. High HP and armor, blunt offense.",
        "stat_bonuses": {"BHP": 5, "CON": 1, "AC": 1},
        "starting_weapon": "Short Sword",
        "starting_potions": ["Healing Potion"],
    },

    {
        "name": "Rogue",
        "description": "Quick and cunning, relying on speed and precision over raw strength.",
        "stat_bonuses": {"ATK": 1,  "EVA": 1, "DEX": 1},
        "starting_weapon": "Dagger",
        "starting_potions": ["Healing Potion"],
    },
    {
        "name": "Mage",
        "description": "Frail in body but powerful in mind, wielding intellect over muscle.",
        "stat_bonuses": {"INT": 1, "PWR": 1, "BMP":5},
        "starting_weapon": "Wand",
        "starting_potions": ["Healing Potion"],
    },
    {
        "name": "Ranger",
        "description": "A resilient tracker balancing survival instincts with sharp wits.",
        "stat_bonuses": {"ACC": 1, "RES": 1, "STR": 1},
        "starting_weapon": "Short Bow",
        "starting_potions": ["Healing Potion"],
    },
]


def starting_gear_for(class_):
    """Build actual Item instances for a class's starting kit."""
    gear = []
    if class_.get("starting_weapon"):
        gear.append(_weapon(class_["starting_weapon"]))
    for potion_name in class_.get("starting_potions", []):
        gear.append(_potion(potion_name))
    return gear
