"""Combat-capable entities: Monster and Player."""

import random


class Monster:
    def __init__(self, name, hp, attack_min, attack_max, EVA=0, PER=0, XP=0, GOLD=0):
        self.name = name
        self.hp = hp
        self.max_hp = hp
        self.attack_min = attack_min
        self.attack_max = attack_max
        self.EVA = EVA
        self.PER = PER
        self.XP = XP
        self.GOLD = GOLD

    @property
    def alive(self):
        return self.hp > 0

    def attack(self):
        return random.randint(self.attack_min, self.attack_max)


class Player:
    # Every character starts from this baseline before race/class bonuses
    # are layered on top of it in Player.create().
    BASE_STATS = {"CON": 5, "STR": 5, "DEX": 5, "INT": 5}

    BONUS_STATS ={ "BHP": 0, "AC": 0, "EVA": 0, "BMP": 0}

    def __init__(self, HP=20, attack_min=1, attack_max=5, CON=0, STR=0, DEX=0, INT=0, LVL=1, AC=0, XP=0, EVA=0, MP=0, BHP=0, name="Adventurer"):
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

        hp = 10 + (stats["CON"]*2) + flat_stats["BHP"]
        attack_min = max(1, 1 + stats["STR"] // 3)
        attack_max = max(attack_min + 1, 4 + stats["STR"] // 2)
        ac = max(0, stats["DEX"] // 3) + flat_stats["AC"]
        eva = max(0, stats["DEX"] // 2) + flat_stats["EVA"]
        mp = max(0, stats["INT"] * 2) +flat_stats["BMP"]

        player = cls(
            HP=hp, attack_min=attack_min, attack_max=attack_max,
            CON=stats["CON"], STR=stats["STR"], DEX=stats["DEX"], INT=stats["INT"],
            LVL=1, AC=ac, XP=0, EVA=eva, MP=mp, name=name,
        )
        player.race = race["name"]
        player.class_name = class_["name"]
        return player

    def attack(self):
        base = random.randint(self.attack_min, self.attack_max)
        bonus = self.equipped_weapon.attack_bonus if self.equipped_weapon else 0
        return base + bonus

    def heal(self, amount):
        self.hp = min(self.max_hp, self.hp + amount)
