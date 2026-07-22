"""Combat-capable entities: Monster and Player."""

import random


class Monster:
    def __init__(self, name, hp, attack_min, attack_max, EVA=0, PER=0, XP=0, GOLD=0, ACC=0):
        self.name = name
        self.hp = hp
        self.max_hp = hp
        self.attack_min = attack_min
        self.attack_max = attack_max
        self.EVA = EVA
        self.PER = PER
        self.XP = XP
        self.GOLD = GOLD
        self.ACC = ACC

    @property
    def alive(self):
        return self.hp > 0

    def attack(self):
        return _triangular_roll(self.attack_min, self.attack_max)


def _triangular_roll(low, high):
    """Roll damage with a mode at the high end of the range."""
    if low >= high:
        return low
    return max(low, min(high, round(random.triangular(low, high, high))))


class Player:
    # Every character starts from this baseline before race/class bonuses
    # are layered on top of it in Player.create().
    BASE_STATS = {"CON": 5, "STR": 5, "DEX": 5, "INT": 5}

    BONUS_STATS = {"BHP": 0, "AC": 0, "EVA": 0, "BMP": 0, "ATK": 0}

    def __init__(self, HP=20, attack_min=0, attack_max=4, CON=0, STR=0, DEX=0, INT=0, LVL=1, AC=0, XP=0, EVA=0, MP=0, BHP=0, ATK=0, name="Adventurer"):
        self.name = name
        self.race = None        # race name, set by Player.create()
        self.class_name = None  # class name, set by Player.create()
        self.hp = HP
        self.max_hp = HP
        self.BHP = BHP
        self.attack_min = attack_min
        self.attack_max = attack_max
        self.CON = CON
        self.AC = AC
        self.STR = STR
        self.DEX = DEX
        self.INT = INT
        self.LVL = LVL
        self.XP = XP    
        self.EVA = EVA
        self.MP = MP
        self.ATK = ATK
        self.inventory = []       # list of Item
        self.equipped_weapon = None

    @property
    def alive(self):
        return self.hp > 0

    @classmethod
    def create(cls, name, race, class_):
        """
        Build a Player from a race dict and a class dict (see races.py /
        classes.py). Stat bonuses from both are added onto BASE_STATS,
        then HP/attack/AC/EVA/MANA are derived from the resulting stats.

        These derivation formulas are a first pass and easy to retune
        later without touching anything else that uses Player.
        """
        stats = dict(cls.BASE_STATS)
        for stat, bonus in race.get("stat_bonuses", {}).items():
            stats[stat] = stats.get(stat, 0) + bonus
        for stat, bonus in class_.get("stat_bonuses", {}).items():
            stats[stat] = stats.get(stat, 0) + bonus

        flat_stats = dict(cls.BONUS_STATS)
        for stat, bonus in race.get("stat_bonuses", {}).items():
            flat_stats[stat] = flat_stats.get(stat, 0) + bonus
        for stat, bonus in class_.get("stat_bonuses", {}).items():
            flat_stats[stat] = flat_stats.get(stat, 0) + bonus

        hp = 10 + (stats["CON"]*5) + flat_stats["BHP"]
        attack_min, attack_max = 0, 4
        ac = max(0, stats["DEX"] // 5) + flat_stats["AC"]
        eva = max(0, stats["DEX"] // 2) + flat_stats["EVA"]
        mp = max(0, stats["INT"]) +flat_stats["BMP"]

        player = cls(
            HP=hp, attack_min=attack_min, attack_max=attack_max,
            CON=stats["CON"], STR=stats["STR"], DEX=stats["DEX"], INT=stats["INT"],
            LVL=1, AC=ac, XP=0, EVA=eva, MP=mp, BHP=flat_stats["BHP"],
            ATK=flat_stats["ATK"], name=name,
        )
        player.race = race["name"]
        player.class_name = class_["name"]
        return player

    def attack(self):
        low, high = self.damage_range
        return _triangular_roll(low, high)

    @property
    def attack_bonus(self):
        """Total ATK applied to both ends of the equipped damage range."""
        if self.equipped_weapon is None:
            return self.ATK
        excess_strength = max(0, self.STR - self.equipped_weapon.str_req)
        return self.ATK + self.equipped_weapon.attack_bonus + excess_strength // 2

    @property
    def damage_range(self):
        if self.equipped_weapon is None:
            base_min, base_max = 0, 4
        else:
            base_min = self.equipped_weapon.damage_min
            base_max = self.equipped_weapon.damage_max
        bonus = self.attack_bonus
        return base_min + bonus, base_max + bonus

    def heal(self, amount):
        self.hp = min(self.max_hp, self.hp + amount)
