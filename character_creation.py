"""Interactive character creation: race + class selection, then a
finished Player built from Player.create()."""

from entities import Player
from races import RACES
from classes import CLASSES, starting_gear_for


def _prompt_choice(options, label):
    print(f"\nChoose your {label}:")
    for i, opt in enumerate(options, start=1):
        print(f"  {i}. {opt['name']} - {opt['description']}")
        bonuses = ", ".join(
            f"{stat} {value:+d}" for stat, value in opt["stat_bonuses"].items() if value != 0
        )
        if bonuses:
            print(f"     ({bonuses})")
    while True:
        raw = input(f"Enter a number (1-{len(options)}): ").strip()
        if raw.isdigit() and 1 <= int(raw) <= len(options):
            return options[int(raw) - 1]
        print("That's not a valid choice.")


def create_character():
    print("=" * 50)
    print("  CHARACTER CREATION")
    print("=" * 50)

    race = _prompt_choice(RACES, "race")
    class_ = _prompt_choice(CLASSES, "class")

    name = input("\nName your character (leave blank for 'Adventurer'): ").strip()
    if not name:
        name = "Adventurer"

    player = Player.create(name, race, class_)

    for item in starting_gear_for(class_):
        player.inventory.append(item)
        if hasattr(item, "attack_bonus") and player.equipped_weapon is None:
            player.equipped_weapon = item

    print(f"\n{name} the {race['name']} {class_['name']} is ready.")
    print(
        f"HP: {player.hp}  STR: {player.STR}  CON: {player.CON}  "
        f"DEX: {player.DEX}  INT: {player.INT}  AC: {player.AC}  "
        f"EVA: {player.EVA}  MP: {player.MP}"
    )
    if player.inventory:
        print("Starting items: " + ", ".join(item.name for item in player.inventory))

    return player
