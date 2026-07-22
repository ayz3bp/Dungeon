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
  take <item>         - pick up an item from the room
  drop <item>         - drop an item from your inventory
  use <item>          - drink a potion or equip a weapon
  inventory           - show what you're carrying
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
        location = f"Depth {state.depth} (Act {state.act})" if state.in_dungeon else "Camp"
        print(f"{p.name} the {p.race} {p.class_name}")
        print(
            f"HP: {p.hp}/{p.max_hp}  MP: {p.MP}  |  "
            f"ATK: {p.attack_bonus}  "
            f"AC: {p.AC}  EVA: {p.EVA} " 
            f"PWR: {p.PWR} "
            f"RES: {p.RES} "
        )
        print(
            f"CON: {p.CON}  STR: {p.STR}  DEX: {p.DEX}  INT: {p.INT}  |  "
            f"Level: {p.LVL}  XP: {p.XP}"
        )
        print(f"Weapon: {weapon}  |  Location: {location}")

    elif verb in ("take", "get", "pickup"):
        state.take(rest)

    elif verb == "drop":
        state.drop(rest)

    elif verb == "use":
        state.use(rest)

    elif verb == "inventory" or verb == "i":
        if not state.player.inventory:
            print("You aren't carrying anything.")
        else:
            for item in state.player.inventory:
                tag = " (equipped)" if item is state.player.equipped_weapon else ""
                if hasattr(item, "damage_min"):
                    details = (
                        f" [{item.damage_min}-{item.damage_max} damage, "
                        f"STR Req {item.str_req}, ATK +{item.attack_bonus}]"
                    )
                else:
                    details = ""
                print(f"  {item.name}{tag}{details} - {item.description}")

    elif verb == "help":
        print(HELP_TEXT)

    elif verb in ("quit", "exit", "q"):
        print("Farewell, adventurer.")
        state.running = False

    else:
        print(f"I don't understand '{verb}'. Type 'help' for a list of commands.")
