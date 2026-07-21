"""
Text-based ASCII dungeon crawler - Stage 1 skeleton
Room graph + simple command parser (look, go <direction>, quit)
"""

import random
import sys
from collections import deque


class Monster:
    def __init__(self, name, hp, attack_min, attack_max):
        self.name = name
        self.hp = hp
        self.max_hp = hp
        self.attack_min = attack_min
        self.attack_max = attack_max

    @property
    def alive(self):
        return self.hp > 0

    def attack(self):
        return random.randint(self.attack_min, self.attack_max)


class Item:
    """Base class for anything that can be picked up."""
    def __init__(self, name, description):
        self.name = name
        self.description = description


class Weapon(Item):
    def __init__(self, name, description, attack_bonus):
        super().__init__(name, description)
        self.attack_bonus = attack_bonus


class Potion(Item):
    def __init__(self, name, description, heal_amount):
        super().__init__(name, description)
        self.heal_amount = heal_amount


class Player:
    def __init__(self, hp=20, attack_min=2, attack_max=6):
        self.hp = hp
        self.max_hp = hp
        self.attack_min = attack_min
        self.attack_max = attack_max
        self.inventory = []       # list of Item
        self.equipped_weapon = None

    @property
    def alive(self):
        return self.hp > 0

    def attack(self):
        base = random.randint(self.attack_min, self.attack_max)
        bonus = self.equipped_weapon.attack_bonus if self.equipped_weapon else 0
        return base + bonus

    def heal(self, amount):
        self.hp = min(self.max_hp, self.hp + amount)


class Room:
    def __init__(self, name, description):
        self.name = name
        self.description = description
        self.exits = {}      # direction (str) -> Room
        self.monsters = []   # placeholder for stage 2
        self.items = []      # placeholder for stage 3
        self.coord = None    # (x, y) grid position, set during generation

    def connect(self, direction, other_room, bidirectional=True):
        """Link this room to another room in a given direction."""
        opposite = {
            "north": "south",
            "south": "north",
            "east": "west",
            "west": "east",
        }
        self.exits[direction] = other_room
        if bidirectional and direction in opposite:
            other_room.exits[opposite[direction]] = self

    def describe(self):
        lines = [f"== {self.name} ==", self.description]
        if self.exits:
            exit_list = ", ".join(sorted(self.exits.keys()))
            lines.append(f"Exits: {exit_list}")
        else:
            lines.append("There are no obvious exits.")
        living = [m for m in self.monsters if m.alive]
        if living:
            lines.append(
                "You see: " + ", ".join(f"{m.name} ({m.hp}/{m.max_hp} HP)" for m in living)
            )
        if self.items:
            lines.append("Items here: " + ", ".join(i.name for i in self.items))
        return "\n".join(lines)


class GameState:
    def __init__(self, starting_room, player):
        self.current_room = starting_room
        self.player = player
        self.turn_count = 0
        self.running = True
        self.visited = {starting_room}

    def move(self, direction):
        living_here = [m for m in self.current_room.monsters if m.alive]
        if living_here:
            names = ", ".join(m.name for m in living_here)
            print(f"You can't leave — the {names} is blocking your way! Fight or flee.")
            return
        if direction in self.current_room.exits:
            self.current_room = self.current_room.exits[direction]
            self.visited.add(self.current_room)
            self.turn_count += 1
            print(self.current_room.describe())
        else:
            print("You can't go that way.")

    def find_monster(self, name_fragment):
        """Find a living monster in the current room by partial name match."""
        name_fragment = name_fragment.lower()
        for m in self.current_room.monsters:
            if m.alive and name_fragment in m.name.lower():
                return m
        return None

    def attack(self, target_name):
        if not target_name:
            living = [m for m in self.current_room.monsters if m.alive]
            if not living:
                print("There's nothing here to attack.")
                return
            target = living[0]
        else:
            target = self.find_monster(target_name)
            if target is None:
                print(f"There's no '{target_name}' here to attack.")
                return

        # Player swings first.
        dmg = self.player.attack()
        target.hp = max(0, target.hp - dmg)
        print(f"You hit the {target.name} for {dmg} damage. ({target.hp}/{target.max_hp} HP)")

        if not target.alive:
            print(f"The {target.name} collapses. You are victorious!")
            self.turn_count += 1
            return

        # Monster retaliates.
        retaliation = target.attack()
        self.player.hp = max(0, self.player.hp - retaliation)
        print(
            f"The {target.name} claws back for {retaliation} damage. "
            f"({self.player.hp}/{self.player.max_hp} HP)"
        )
        self.turn_count += 1

        if not self.player.alive:
            print("\nYou have died. Game over.")
            self.running = False

    def flee(self, direction):
        """Attempt to escape combat by moving, ignoring the monster-blocks-exit rule."""
        if direction in self.current_room.exits:
            self.current_room = self.current_room.exits[direction]
            self.visited.add(self.current_room)
            self.turn_count += 1
            print(f"You break away and flee {direction}!")
            print(self.current_room.describe())
        else:
            print("You can't flee that way.")

    def render_map(self):
        """
        Build an ASCII minimap from rooms the player has actually visited.
        Known-but-unvisited rooms (an exit of a visited room you haven't
        stepped into yet) are shown as '?' so you know a passage exists
        without revealing what's there.
        """
        # symbol for every coordinate we have some knowledge of
        symbols = {}   # coord -> '@' / 'o' / '?'
        connectors = set()  # frozenset({coord_a, coord_b}) for each known passage

        def symbol_for(room):
            if room is self.current_room:
                return "@"
            if room in self.visited:
                return "o"
            return "?"

        for room in self.visited:
            coord = room.coord
            symbols[coord] = symbol_for(room)
            for neighbor in room.exits.values():
                n_coord = neighbor.coord
                # Don't downgrade a cell we already know is visited/current.
                if n_coord not in symbols or symbols[n_coord] == "?":
                    symbols[n_coord] = symbol_for(neighbor)
                connectors.add(frozenset({coord, n_coord}))

        if not symbols:
            return "(no map data yet)"

        xs = [c[0] for c in symbols]
        ys = [c[1] for c in symbols]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)

        width = 2 * (max_x - min_x) + 1
        height = 2 * (max_y - min_y) + 1
        grid = [[" "] * width for _ in range(height)]

        def cell(coord):
            x, y = coord
            return (2 * (max_y - y), 2 * (x - min_x))  # (row, col); north = up

        for coord, sym in symbols.items():
            row, col = cell(coord)
            grid[row][col] = sym

        for pair in connectors:
            coord_a, coord_b = tuple(pair)
            row_a, col_a = cell(coord_a)
            row_b, col_b = cell(coord_b)
            if col_a == col_b:  # vertical passage (north/south)
                row = (row_a + row_b) // 2
                grid[row][col_a] = "|"
            elif row_a == row_b:  # horizontal passage (east/west)
                col = (col_a + col_b) // 2
                grid[row_a][col] = "-"

        map_lines = ["".join(row).rstrip() for row in grid]
        legend = "@ = you   o = visited   ? = known passage, unexplored"
        return "\n".join(map_lines) + "\n\n" + legend

    def find_item_in_room(self, name_fragment):
        name_fragment = name_fragment.lower()
        for item in self.current_room.items:
            if name_fragment in item.name.lower():
                return item
        return None

    def find_item_in_inventory(self, name_fragment):
        name_fragment = name_fragment.lower()
        for item in self.player.inventory:
            if name_fragment in item.name.lower():
                return item
        return None

    def take(self, name_fragment):
        if not name_fragment:
            print("Take what?")
            return
        item = self.find_item_in_room(name_fragment)
        if item is None:
            print(f"There's no '{name_fragment}' here.")
            return
        self.current_room.items.remove(item)
        self.player.inventory.append(item)
        print(f"You pick up the {item.name}.")

        if item.name == "Ancient Amulet":
            print(
                "\nThe amulet pulses with ancient power as your fingers close around it.\n"
                "You have recovered the Ancient Amulet. VICTORY!"
            )
            self.running = False

    def drop(self, name_fragment):
        if not name_fragment:
            print("Drop what?")
            return
        item = self.find_item_in_inventory(name_fragment)
        if item is None:
            print(f"You aren't carrying a '{name_fragment}'.")
            return
        self.player.inventory.remove(item)
        self.current_room.items.append(item)
        if self.player.equipped_weapon is item:
            self.player.equipped_weapon = None
            print(f"You unequip and drop the {item.name}.")
        else:
            print(f"You drop the {item.name}.")

    def use(self, name_fragment):
        if not name_fragment:
            print("Use what?")
            return
        item = self.find_item_in_inventory(name_fragment)
        if item is None:
            print(f"You aren't carrying a '{name_fragment}'.")
            return

        if isinstance(item, Potion):
            self.player.heal(item.heal_amount)
            self.player.inventory.remove(item)
            print(
                f"You drink the {item.name} and recover {item.heal_amount} HP. "
                f"({self.player.hp}/{self.player.max_hp} HP)"
            )
        elif isinstance(item, Weapon):
            self.player.equipped_weapon = item
            print(f"You equip the {item.name} (+{item.attack_bonus} attack).")
        else:
            print(f"You can't figure out how to use the {item.name}.")


ROOM_THEMES = [
    ("Dungeon Entrance", "A crumbling stone archway leads down into darkness. Torchlight flickers weakly on damp walls."),
    ("Long Hall", "A narrow hallway stretches out, lined with cracked pillars."),
    ("Sunken Chamber", "The floor slopes down into a flooded chamber. Old bones litter the shallows."),
    ("Collapsed Passage", "Rubble chokes half the corridor. A thin gap remains passable."),
    ("Fungal Grotto", "Pale mushrooms cast a faint blue glow across damp stone."),
    ("Bone Ossuary", "Skulls are stacked floor to ceiling in neat, unsettling rows."),
    ("Forgotten Library", "Rotted shelves spill crumbling tomes across the floor."),
    ("Ritual Chamber", "A cracked stone altar dominates the room, stained dark."),
    ("Cistern", "Still black water fills a sunken basin. Something ripples beneath it."),
    ("Guard Post", "A rusted rack of weapons leans against the wall, mostly picked clean."),
    ("Crypt Alcove", "Shallow tombs line the walls, their seals long broken."),
    ("Twisting Stair", "A spiral stairwell descends further than torchlight can reach."),
    ("Root Cellar", "Thick roots have broken through the stone from somewhere above."),
    ("Shattered Vault", "A heavy door hangs off its hinges, the vault beyond emptied long ago."),
    ("Echoing Cavern", "Every footstep returns as a hollow, doubled echo."),
]

MONSTER_TEMPLATES = [
    {"name": "Giant Rat",      "hp": (6, 10),  "atk": (1, 3),  "tier": 1, "weight": 5},
    {"name": "Cave Spider",    "hp": (8, 12),  "atk": (2, 4),  "tier": 1, "weight": 4},
    {"name": "Skeleton",       "hp": (10, 16), "atk": (2, 5),  "tier": 1, "weight": 3},
    {"name": "Goblin Grunt",   "hp": (12, 18), "atk": (3, 6),  "tier": 2, "weight": 4},
    {"name": "Rot Zombie",     "hp": (16, 22), "atk": (3, 7),  "tier": 2, "weight": 3},
    {"name": "Crypt Wight",    "hp": (18, 24), "atk": (4, 8),  "tier": 2, "weight": 2},
    {"name": "Dungeon Ogre",   "hp": (25, 35), "atk": (5, 10), "tier": 3, "weight": 2},
    {"name": "Shadow Wraith",  "hp": (20, 28), "atk": (6, 12), "tier": 3, "weight": 2},
]

WEAPON_TEMPLATES = [
    {"name": "Rusty Dagger", "description": "Small, quick, and none too sharp anymore.", "bonus": (1, 2)},
    {"name": "Iron Sword",   "description": "A plain but well-balanced blade.", "bonus": (3, 4)},
    {"name": "Spiked Mace",  "description": "Heavy and brutal, built to crush.", "bonus": (4, 6)},
    {"name": "War Axe",      "description": "A two-handed axe notched from hard use.", "bonus": (5, 7)},
]

POTION_TEMPLATES = [
    {"name": "Minor Healing Potion", "description": "A thin, watery tonic. Better than nothing.", "heal": (5, 8)},
    {"name": "Healing Potion",       "description": "A dull red vial that smells faintly of herbs.", "heal": (10, 15)},
    {"name": "Greater Healing Potion", "description": "Thick, glowing liquid — clearly potent.", "heal": (16, 22)},
]

DIRECTIONS = {"north": (0, 1), "south": (0, -1), "east": (1, 0), "west": (-1, 0)}


def _weighted_choice(templates):
    total = sum(t["weight"] for t in templates)
    roll = random.uniform(0, total)
    upto = 0
    for t in templates:
        upto += t["weight"]
        if roll <= upto:
            return t
    return templates[-1]


def _bfs_distances(entry):
    """Distance (in rooms) from the entry to every reachable room."""
    dist = {entry: 0}
    queue = deque([entry])
    while queue:
        room = queue.popleft()
        for neighbor in room.exits.values():
            if neighbor not in dist:
                dist[neighbor] = dist[room] + 1
                queue.append(neighbor)
    return dist


def generate_dungeon(num_rooms=8):
    """
    Build a random dungeon as a graph of connected rooms.

    Uses a random walk over a grid of (x, y) coordinates so that compass
    directions stay consistent (going north then south always gets you
    back where you started), then layers in extra loop connections,
    monsters, items, and a goal room holding the win condition.
    """
    themes = ROOM_THEMES[:]
    random.shuffle(themes)

    def next_theme(index):
        return themes[index % len(themes)]

    coord_to_room = {}
    entry = Room(*next_theme(0))
    entry.coord = (0, 0)
    coord_to_room[(0, 0)] = entry
    placed_coords = [(0, 0)]

    theme_index = 1
    attempts = 0
    attempts_cap = num_rooms * 25
    while len(coord_to_room) < num_rooms and attempts < attempts_cap:
        attempts += 1
        base_coord = random.choice(placed_coords)
        direction = random.choice(list(DIRECTIONS.keys()))
        dx, dy = DIRECTIONS[direction]
        new_coord = (base_coord[0] + dx, base_coord[1] + dy)
        if new_coord in coord_to_room:
            continue
        new_room = Room(*next_theme(theme_index))
        new_room.coord = new_coord
        theme_index += 1
        coord_to_room[new_coord] = new_room
        placed_coords.append(new_coord)
        coord_to_room[base_coord].connect(direction, new_room)

    # Add a few extra connections between adjacent rooms so the map isn't
    # purely a tree (occasional shortcuts/loops).
    for coord, room in list(coord_to_room.items()):
        for direction, (dx, dy) in DIRECTIONS.items():
            if direction in room.exits:
                continue
            neighbor_coord = (coord[0] + dx, coord[1] + dy)
            neighbor = coord_to_room.get(neighbor_coord)
            if neighbor is not None and random.random() < 0.15:
                room.connect(direction, neighbor)

    dist = _bfs_distances(entry)
    goal_room = max(dist, key=dist.get)

    for room, depth in dist.items():
        if room is entry or room is goal_room:
            continue

        if random.random() < 0.6:
            tier = 1 if depth <= 1 else (2 if depth <= 3 else 3)
            candidates = [t for t in MONSTER_TEMPLATES if t["tier"] == tier] or MONSTER_TEMPLATES
            template = _weighted_choice(candidates)
            hp = random.randint(*template["hp"])
            atk_min, atk_max = template["atk"]
            room.monsters.append(Monster(template["name"], hp, atk_min, atk_max))

        if random.random() < 0.5:
            if random.random() < 0.5:
                wt = random.choice(WEAPON_TEMPLATES)
                bonus = random.randint(*wt["bonus"])
                room.items.append(Weapon(wt["name"], wt["description"], bonus))
            else:
                pt = random.choice(POTION_TEMPLATES)
                heal = random.randint(*pt["heal"])
                room.items.append(Potion(pt["name"], pt["description"], heal))

    goal_room.items.append(Item(
        "Ancient Amulet",
        "A pulsing amulet radiating ancient power. This is what you came for."
    ))

    return entry


HELP_TEXT = """\
Commands:
  look                - describe the current room again
  map                 - show a minimap of rooms you've explored
  go <direction>      - move (north, south, east, west)
  attack [target]     - attack a monster in the room (defaults to the first one)
  flee <direction>    - break off combat and move to an adjacent room
  status              - show your HP and equipped weapon
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
        print(f"HP: {p.hp}/{p.max_hp}  |  Weapon: {weapon}")

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
                print(f"  {item.name}{tag} - {item.description}")

    elif verb == "help":
        print(HELP_TEXT)

    elif verb in ("quit", "exit", "q"):
        print("Farewell, adventurer.")
        state.running = False

    else:
        print(f"I don't understand '{verb}'. Type 'help' for a list of commands.")


def main():
    seed = None
    if len(sys.argv) > 1:
        try:
            seed = int(sys.argv[1])
            random.seed(seed)
        except ValueError:
            pass

    print("=" * 50)
    print("  ASCII DUNGEON CRAWLER")
    print("=" * 50)
    if seed is not None:
        print(f"(seed: {seed})")
    print("Find the Ancient Amulet buried somewhere in the dungeon below.")
    print(HELP_TEXT)

    entry_room = generate_dungeon(num_rooms=8)
    player = Player()
    state = GameState(entry_room, player)
    print(state.current_room.describe())

    while state.running:
        try:
            raw = input("\n> ")
        except (EOFError, KeyboardInterrupt):
            print("\nFarewell, adventurer.")
            break

        verb, rest = parse_command(raw)
        handle_command(verb, rest, state)

    sys.exit(0)


if __name__ == "__main__":
    main()
