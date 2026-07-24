"""Pickup-able items: base Item plus Weapon and Potion subtypes."""


class Item:
    """Base class for anything that can be picked up."""
    def __init__(self, name, description):
        self.name = name
        self.description = description


PRIMARY_STATS = ("CON", "STR", "DEX", "INT")


def _unmet_requirements(requirements, player):
    """Return {stat: required} for any requirement in `requirements` the
    player doesn't meet. Empty dict means the player can equip the item."""
    return {
        stat: required
        for stat, required in requirements.items()
        if getattr(player, stat, 0) < required
    }


class Weapon(Item):
    def __init__(self, name, description, damage_min, damage_max, requirements=None, attack_bonus=0):
        super().__init__(name, description)
        self.damage_min = damage_min
        self.damage_max = damage_max
        # Maps any of CON/STR/DEX/INT to the minimum value needed to wield
        # this weapon, e.g. {"DEX": 12} or {"STR": 8, "INT": 6}. Omitted
        # stats have no requirement.
        self.requirements = dict(requirements) if requirements else {}
        self.attack_bonus = attack_bonus

    @property
    def str_req(self):
        """Convenience accessor for the STR requirement specifically (0 if
        this weapon has none) — used for the excess-strength attack bonus."""
        return self.requirements.get("STR", 0)

    def unmet_requirements(self, player):
        return _unmet_requirements(self.requirements, player)


class Armor(Item):
    def __init__(self, name, description, block_min, block_max, requirements=None, armor_class=0):
        super().__init__(name, description)
        self.block_min = block_min
        self.block_max = block_max
        # Same shape as Weapon.requirements: any of CON/STR/DEX/INT to a
        # minimum value, e.g. {"CON": 14} or {"DEX": 10}.
        self.requirements = dict(requirements) if requirements else {}
        self.armor_class = armor_class

    @property
    def str_req(self):
        """Convenience accessor for the STR requirement specifically (0 if
        this armor has none)."""
        return self.requirements.get("STR", 0)

    def unmet_requirements(self, player):
        return _unmet_requirements(self.requirements, player)

class Potion(Item):
    """
    A single-use consumable. `kind` picks what effect it has (see
    GameState._apply_potion_effect in world.py for the actual list),
    `power` is that effect's magnitude — a flat number, or a (low, high)
    range rolled the same way weapon damage is. `duration` is a
    placeholder for a future timed-effect system; unused for now.

    Any potion can be drunk (targets yourself) or thrown (targets a
    monster) — see GameState.drink()/throw(). Nothing here restricts a
    given kind to one or the other; that's a player choice, not a rule
    (drinking a harmful one is just a bad idea, not an invalid one).

    To add a new potion: pick a `kind` name, decide what `power` means
    for it, and add one branch for that kind in
    GameState._apply_potion_effect.
    """
    def __init__(self, name, description, kind, power, duration=0):
        super().__init__(name, description)
        self.kind = kind
        self.power = power
        self.duration = duration


class Food(Item):
    def __init__(self, name, description, satiety_restore):
        super().__init__(name, description)
        self.satiety_restore = satiety_restore
