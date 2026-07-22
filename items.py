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


class Potion(Item):
    def __init__(self, name, description, heal_amount):
        super().__init__(name, description)
        self.heal_amount = heal_amount
