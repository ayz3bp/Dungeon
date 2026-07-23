"""Player-facing command layer: parsing raw input and dispatching it
against a GameState."""

HELP_TEXT = """\
Commands:
  look                - describe the current room again
  map                 - show a minimap of rooms you've explored
  enter               - leave camp and descend into the dungeon
  descend             - take the stairs down to the next floor (when present)
  ascend              - take the stairs back up to the previous floor (when present)
  go <direction>      - move (north, south, east, west)
  attack [target]     - attack a monster in the room (defaults to the first one)
  flee <direction>    - break off combat and move to an adjacent room
  status              - show your character stats and current location
  level <stat>        - spend an unspent stat point on CON, STR, DEX, or INT
  take <item>         - pick up an item from the room
  drop <item>         - drop an item from your inventory
  use <item>          - eat food, or equip a weapon/armor
  drink <potion>      - drink a potion yourself
  throw <potion> [at <target>] - throw a potion at a monster (defaults to the first one)
  inventory           - show what you're carrying
  wait [#]            - pass a number of turns (default 1) doing nothing else
  help                - show this message
  quit                - exit the game
"""


def parse_command(raw_input):
    """Split raw input into a verb and the rest of the arguments."""
    parts = raw_input.strip().lower().split()
    if not parts:
        return "", ""
    verb = parts[0]
    rest = " ".join(parts[1:])
    return verb, rest


def handle_command(verb, rest, state):
    if verb in ("look", "l"):
        print(state.current_room.describe())

    elif verb == "map":
        print(state.render_map())

    elif verb == "enter":
        state.enter_dungeon()

    elif verb == "descend":
        state.descend()

    elif verb == "ascend":
        state.ascend()

    elif verb in ("go", "move") or verb in ("north", "south", "east", "west"):
        direction = rest if verb in ("go", "move") else verb
        if not direction:
            print("Go where? (try: go north)")
        else:
            state.move(direction)

    elif verb in ("attack", "a", "fight"):
        state.attack(rest)

    elif verb == "flee":
        if not rest:
            print("Flee which direction? (try: flee south)")
        else:
            state.flee(rest)

    elif verb == "status":
        p = state.player
        weapon = p.equipped_weapon.name if p.equipped_weapon else "none"
        armor = p.equipped_armor.name if p.equipped_armor else "none"
        location = f"Depth {state.depth} (Act {state.act})" if state.in_dungeon else "Camp"
        xp_display = (
            f"{p.XP}/{p.xp_to_next_level}" if p.xp_to_next_level is not None else f"{p.XP} (MAX)"
        )
        print(f"{p.name} the {p.race} {p.class_name}")
        print(
            f"HP: {p.hp}/{p.max_hp}  MP: {p.MP}/{p.max_MP}  |  "
            f"REG: {p.REG}  "  
            f"MPG: {p.MPG}  "
            f"ATK: {p.attack_bonus}  "
            f"AC: {p.AC}  "
            f"EVA: {p.EVA}  " 
            f"PWR: {p.PWR}  "
            f"RES: {p.RES}  "
            f"ACC: {p.ACC}  "
        )
        print(
            f"CON: {p.CON}  STR: {p.STR}  DEX: {p.DEX}  INT: {p.INT}  |  "
            f"Level: {p.LVL}  XP: {xp_display}"
        )
        print(f"Weapon: {weapon}  |  Armor: {armor}  |  Location: {location}  |  Gold: {p.gold}")
        if p.hunger_tier != "full":
            print(f"Satiety: {p.satiety:.0f}/100  ({p.hunger_tier})")
        else:
            print(f"Satiety: {p.satiety:.0f}/100")
        if p.unspent_stat_points > 0:
            print(f"You have {p.unspent_stat_points} unspent stat point(s).")

    elif verb == "level":
        if not rest:
            print("Spend a stat point on which stat?")
        else:
            success, message = state.player.spend_stat_point(rest)
            print(message)

    elif verb in ("take", "get", "pickup"):
        state.take(rest)

    elif verb == "drop":
        state.drop(rest)

    elif verb == "use":
        state.use(rest)

    elif verb == "drink":
        state.drink(rest)

    elif verb == "throw":
        if not rest:
            print("Throw what? (try: throw vial at goblin)")
        else:
            if " at " in rest:
                item_part, _, target_part = rest.partition(" at ")
            else:
                item_part, target_part = rest, ""
            state.throw(item_part.strip(), target_part.strip())

    elif verb == "inventory" or verb == "i":
        if not state.player.inventory:
            print("You aren't carrying anything.")
        else:
            for item in state.player.inventory:
                if item is state.player.equipped_weapon or item is state.player.equipped_armor:
                    tag = " (equipped)"
                else:
                    tag = ""
                if hasattr(item, "damage_min"):
                    details = (
                        f" [{item.damage_min}-{item.damage_max} damage, "
                        f"STR Req {item.str_req}, ATK +{item.attack_bonus}]"
                    )
                elif hasattr(item, "block_min"):
                    details = (
                        f" [{item.block_min}-{item.block_max} block, "
                        f"STR Req {item.str_req}]"
                    )
                elif hasattr(item, "satiety_restore"):
                    details = f" [restores {item.satiety_restore} satiety]"
                elif hasattr(item, "kind"):
                    details = f" [{item.kind}, power {item.power}]"
                else:
                    details = ""
                print(f"  {item.name}{tag}{details} - {item.description}")

    elif verb == "help":
        print(HELP_TEXT)

    elif verb in ("quit", "exit", "q"):
        print("Farewell, adventurer.")
        state.running = False

    elif verb == "wait":
        if not rest:
            turns = 1
        else:
            try:
                turns = float(rest)
            except ValueError:
                print(f"'{rest}' isn't a number of turns. (try: wait 2)")
                return
            if turns <= 0:
                print("You can't wait for a non-positive number of turns.")
                return
        turns_display = int(turns) if turns == int(turns) else turns
        print(f"You wait for {turns_display} turn(s), gathering your thoughts and energy.")
        state.advance_turns(turns)

    else:
        print(f"I don't understand '{verb}'. Type 'help' for a list of commands.")
