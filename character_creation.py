"""Interactive character creation: race + class selection, then a
finished Player built from Player.create()."""

from entities import Player
from races import RACES
from classes import CLASSES, starting_gear_for


def _prompt_choice(options, label):
    print(f"\nChoose your {label}:")
    for i, opt in enumerate(options, start=1):
        print(f"  {i}. {opt['name']} : {opt['description']}")
        bonuses = ", ".join(
            f"{stat} {value:+d}" for stat, value in opt["stat_bonuses"].items() if value != 0
        )
        if bonuses:
            print(f"     ({bonuses})")
    while True:
        raw = input(f"Enter a {label} name: ").strip()
        selected_name = raw.casefold()
        for option in options:
            if option["name"].casefold() == selected_name:
                return option

        # Keep numbered choices working for existing players and scripts.
        if raw.isdigit() and 1 <= int(raw) <= len(options):
            return options[int(raw) - 1]
        valid_names = ", ".join(option["name"] for option in options)
        print(f"That's not a valid choice. Enter one of: {valid_names}.")


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
        if (
            hasattr(item, "damage_min")
            and player.equipped_weapon is None
            and player.STR >= item.str_req
        ):
            player.equipped_weapon = item

    print(f"\n{name} the {race['name']} {class_['name']} is ready.")

    if player.inventory:
        print("Starting items: " + ", ".join(item.name for item in player.inventory))

    return player
