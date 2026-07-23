"""Pickup-able items: base Item plus Weapon and Potion subtypes."""


class Item:
    """Base class for anything that can be picked up."""
    def __init__(self, name, description):
        self.name = name
        self.description = description


class Weapon(Item):
    def __init__(self, name, description, damage_min, damage_max, str_req=0, attack_bonus=0):
        super().__init__(name, description)
        self.damage_min = damage_min
        self.damage_max = damage_max
        self.str_req = str_req
        self.attack_bonus = attack_bonus

class Armor(Item):
    def __init__(self, name, description, block_min, block_max, str_req=0, armor_class=0):
        super().__init__(name, description)
        self.block_min = block_min
        self.block_max = block_max
        self.str_req = str_req
        self.armor_class = armor_class

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
