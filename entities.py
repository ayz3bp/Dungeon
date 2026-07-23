"""Combat-capable entities: Monster and Player."""

import math
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


# Stat penalty applied at each hunger tier (a flat amount subtracted from
# the named stat while that tier is active). "wasting" carries the same
# stat penalty as "starving" — its extra bite is the per-turn HP loss,
# handled separately in Player.tick_hunger.
HUNGER_PENALTIES = {
    "full":     {"CON": 0, "STR": 0, "DEX": 0, "INT": 0},
    "hungry":   {"CON": 0, "STR": 1, "DEX": 1, "INT": 0},
    "starving": {"CON": 1, "STR": 1, "DEX": 1, "INT": 1},
    "wasting":  {"CON": 1, "STR": 1, "DEX": 1, "INT": 1},
}


def _hunger_tier_for(satiety):
    """Map a satiety value onto a hunger tier name."""
    if satiety <= -50:
        return "wasting"
    if satiety <= 0:
        return "starving"
    if satiety <= 25:
        return "hungry"
    return "full"


# Message printed whenever satiety crosses into a given tier, whichever
# direction it came from (draining via tick_hunger, or recovering via
# Player.eat()).
TIER_MESSAGES = {
    "full": "You feel fully sated.",
    "hungry": "You are hungry. (-1 STR, -1 DEX)",
    "starving": "You are starving. (-1 to all stats)",
    "wasting": "You are wasting away...",
}


class Player:
    # Every character starts from this baseline before race/class bonuses
    # are layered on top of it in Player.create().
    BASE_STATS = {"CON": 5, "STR": 5, "DEX": 5, "INT": 5, "LVL": 1}

    BONUS_STATS = {"BHP": 0, "AC": 0, "EVA": 0, "BMP": 0, "ATK": 0, "RES": 0, "PWR": 0, "ACC": 0, "REG": 1, "MPG": 5}

    # XP_TO_LEVEL[i] is the XP needed to advance from level (i + 1) to (i + 2).
    # e.g. XP_TO_LEVEL[0] == 10 is the cost of going from level 1 to level 2.
    XP_TO_LEVEL = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100,
                   110, 120, 130, 140, 150, 160, 170, 180, 190, 200]
    MAX_LEVEL = len(XP_TO_LEVEL) + 1  # 21

    def __init__(self, HP=20, attack_min=0, attack_max=4, CON=0, STR=0, DEX=0, INT=0, LVL=1, AC=0, XP=0, EVA=0, MP=0, BMP=0, BHP=0, ATK=0, RES=0, PWR = 0, ACC=0, REG=0, MPG=0, name="Adventurer"):
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
        self.max_MP = MP
        self.MP = MP
        self.BMP = BMP
        self.ATK = ATK
        self.RES = RES
        self.PWR = PWR
        self.ACC = ACC
        self.REG = REG
        self.MPG = MPG
        self.gold = 0
        self.unspent_stat_points = 0
        self.flat_bonuses = dict(self.BONUS_STATS)
        self.satiety = 100.0
        self.hunger_tier = "full"
        self._hunger_penalty = dict(HUNGER_PENALTIES["full"])
        self._wasting_accum = 0.0
        self._regen_accum = 0.0
        self.inventory = []       # list of Item
        self.equipped_weapon = None
        self.equipped_armor = None

    @property
    def alive(self):
        return self.hp > 0

    @property
    def xp_to_next_level(self):
        """XP required to reach the next level, or None if already at MAX_LEVEL."""
        if self.LVL >= self.MAX_LEVEL:
            return None
        return self.XP_TO_LEVEL[self.LVL - 1]

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

        player = cls(
            attack_min=0, attack_max=4,
            CON=stats["CON"], STR=stats["STR"], DEX=stats["DEX"], INT=stats["INT"],
            LVL=1, XP=0, BHP=flat_stats["BHP"], ATK=flat_stats["ATK"],
            BMP=flat_stats["BMP"], REG=flat_stats["REG"], MPG=flat_stats["MPG"], name=name,
        )

        player.flat_bonuses = flat_stats
        player.recompute_derived_stats()
        player.hp = player.max_hp
        player.MP = player.max_MP

        player.race = race["name"]
        player.class_name = class_["name"]
        return player

    def recompute_derived_stats(self):
        """
        Recalculate every stat derived from CON/STR/DEX/INT/LVL plus the
        character's fixed race/class bonuses (self.flat_bonuses). Called
        whenever LVL or a primary stat changes (leveling up, spending a
        stat point) so derived stats never drift out of sync.

        Current HP/MP are left untouched here — callers that want to heal
        on top of a stat change (e.g. the level-up HP/MP recovery) do that
        separately, since max_hp/max_MP may change as a side effect of
        this method.
        """
        b = self.flat_bonuses
        self.max_hp = (self.LVL * 2) + (self.CON * 5) + b["BHP"]
        self.AC = max(0, self.CON // 5) + b["AC"]
        self.RES = max(0, self.CON // 10) + b["RES"]
        self.PWR = max(0, self.INT) + b["PWR"]
        self.EVA = 2 + max(0, self.DEX // 2) + max(0, self.LVL // 2) + b["EVA"]
        self.ACC = 6 + max(0, self.LVL) + b["ACC"]
        self.max_MP = max(0, self.INT * 2) + b["BMP"] + self.LVL
        self.REG = max(1, self.CON // 5) + b["REG"]
        self.MPG = max(5, self.INT // 5) + b["MPG"]

    def gain_xp(self, amount):
        """
        Award XP and process however many level-ups it triggers (a big
        enough haul can chain multiple levels at once). Each level-up
        grants one unspent stat point and recovers 20% of missing HP/MP.
        Returns the list of new levels reached (empty if none).
        """
        self.XP += amount
        levels_gained = []
        while self.xp_to_next_level is not None and self.XP >= self.xp_to_next_level:
            self.XP -= self.xp_to_next_level
            self.LVL += 1
            self.unspent_stat_points += 2

            missing_hp = self.max_hp - self.hp
            missing_mp = self.max_MP - self.MP
            self.recompute_derived_stats()
            self.hp = min(self.max_hp, self.hp + round(missing_hp * 0.2))
            self.MP = min(self.max_MP, self.MP + round(missing_mp * 0.2))

            levels_gained.append(self.LVL)
        return levels_gained

    def spend_stat_point(self, attribute):
        """
        Invest one unspent stat point into CON/STR/DEX/INT. Returns
        (success, message) — success is False if there's no point to
        spend or the attribute name isn't recognized.
        """
        attribute = attribute.strip().upper()
        valid_attributes = ("CON", "STR", "DEX", "INT")

        if self.unspent_stat_points <= 0:
            return False, "You have no stat points to spend."
        if attribute not in valid_attributes:
            return False, f"'{attribute}' isn't a valid stat. Choose from: CON, STR, DEX, INT."

        setattr(self, attribute, getattr(self, attribute) + 1)
        self.unspent_stat_points -= 1
        self.recompute_derived_stats()
        self.hp = min(self.hp, self.max_hp)
        self.MP = min(self.MP, self.max_MP)
        return True, (
            f"{attribute} increased to {getattr(self, attribute)}. "
            f"({self.unspent_stat_points} stat point(s) remaining.)"
        )

    def _sync_hunger_tier(self):
        """
        Recompute the hunger tier from current satiety and apply/remove
        the associated stat penalty if it changed (works in either
        direction — tick_hunger only ever worsens it, Player.eat() only
        ever improves it). Returns the tier-change message, or None if
        the tier didn't change.
        """
        new_tier = _hunger_tier_for(self.satiety)
        if new_tier == self.hunger_tier:
            return None

        target_penalty = HUNGER_PENALTIES[new_tier]
        for stat, target in target_penalty.items():
            delta = self._hunger_penalty[stat] - target
            if delta:
                setattr(self, stat, getattr(self, stat) + delta)
        self._hunger_penalty = dict(target_penalty)
        self.hunger_tier = new_tier
        self.recompute_derived_stats()
        self.hp = min(self.hp, self.max_hp)
        self.MP = min(self.MP, self.max_MP)
        return TIER_MESSAGES[new_tier]

    def tick_hunger(self, turns):
        """
        Advance satiety by `turns` (1 satiety lost per turn elapsed) and
        apply/remove stat penalties when crossing a hunger tier boundary.
        While in the 'wasting' tier, also deals HP damage per turn
        elapsed that escalates the deeper past -50 satiety goes
        (accumulated fractionally so half-turn actions still add up
        correctly). Returns a list of messages to print for whatever
        happened this tick (empty if nothing notable did).
        """
        self.satiety -= turns
        messages = []

        tier_message = self._sync_hunger_tier()
        if tier_message:
            messages.append(tier_message)

        if self.hunger_tier == "wasting":
            depth_below = max(0.0, -50 - self.satiety)
            damage_rate = 1 + int(depth_below // 50)  # +1 per additional -50 satiety
            self._wasting_accum += turns * damage_rate
            dmg = int(self._wasting_accum)
            if dmg:
                self._wasting_accum -= dmg
                self.hp = max(0, self.hp - dmg)
                messages.append(
                    f"Your hunger gnaws at you for {dmg} damage. "
                    f"({self.hp}/{self.max_hp} HP)"
                )

        return messages

    def eat(self, food_name, restore_amount):
        """
        Consume a food item and apply satiety-restore rules:
          - satiety below -50: snap up to -50 first, then add the full
            restore amount on top (a starving character doesn't lose out
            on how deep the hole was)
          - satiety above 100: already full, only a token +25 satiety
          - otherwise: add the full restore amount
        Returns a list of messages to print (the food's own message,
        plus a hunger tier-change message if satiety crossed a
        boundary).
        """
        if self.satiety < -50:
            self.satiety = -50 + restore_amount
            food_message = f"The {food_name} was delicious!"
        elif self.satiety > 100:
            self.satiety += 25
            food_message = "You're too full to enjoy it..."
        else:
            self.satiety += restore_amount
            food_message = f"The {food_name} was delicious!"

        messages = [food_message]
        tier_message = self._sync_hunger_tier()
        if tier_message:
            messages.append(tier_message)
        return messages

    def tick_regen(self, turns):
        """
        Passive regeneration: 1% of max HP/MP (rounded up) every 2 turns
        elapsed, accumulated fractionally like tick_hunger.
        """
        if self.hunger_tier in ("starving", "wasting"):
            return
        self._regen_accum += turns
        while self._regen_accum >= 2:
            self._regen_accum -= 2
            self.hp = min(self.max_hp, self.hp + math.ceil(0.01 *(self.REG) * self.max_hp))
            self.MP = min(self.max_MP, self.MP + math.ceil(0.01 *(self.MPG) * self.max_MP))

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

    def block(self):
        low, high = self.block_range
        return _triangular_roll(low, high)

    @property
    def block_bonus(self):
        """Total AC applied to both ends of the equipped block range."""
        if self.equipped_armor is None:
            return self.AC
        return self.AC + self.equipped_armor.armor_class

    @property
    def block_range(self):
        if self.equipped_armor is None:
            base_min, base_max = 0, 0
        else:
            base_min = self.equipped_armor.block_min
            base_max = self.equipped_armor.block_max
        bonus = self.block_bonus
        return base_min + bonus, base_max + bonus

    def heal(self, amount):
        self.hp = min(self.max_hp, self.hp + amount)
