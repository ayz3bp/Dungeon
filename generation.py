"""Procedural dungeon generation: content tables plus the random-walk
graph builder that lays out rooms, monsters, items, and the goal room."""

import random
from collections import deque

from entities import Monster
from items import Item, Weapon, Potion
from world import Room

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
    ("Dilapidated Treasury", "A vault of broken chests and ransacked gear. The far wall seems unstable..."),
    ("Yawning Chasm", "A massive fissure blocks your path forward. You can barely make out something on the other side..."),
    ("Bloodied Shrine", "A descecrated altar strewn with broken idols and decayed offerings. The air is thick with the scent of iron..."),
    ("Flooded Vault", "Water fills the room. You spot a chest in the distance. You can't see the bottom but something is lurking underneath..."),
    ("Precarious Mine", "An abandoned mine shaft. Mining equipment is strewn about. A reeking stench emanates from the darkness...")
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
    {"name": "Rusty Dagger",    "description": "Small, quick, and none too sharp anymore.",    "damage": (1, 2), "str_req": 5},
    {"name": "Iron Sword",      "description": "A plain but well-balanced blade.",             "damage": (3, 4), "str_req": 7},
    {"name": "Spiked Mace",     "description": "Heavy and brutal, built to crush.",            "damage": (4, 6), "str_req": 8},
    {"name": "War Axe",         "description": "A two-handed axe notched from hard use.",      "damage": (5, 7), "str_req": 8},
    {"name": "Wand",            "description": "A simple yew wand to channel magic.",          "damage": (2, 3), "str_req": 2},
]

POTION_TEMPLATES = [
    {"name": "Healing Potion", "description": "A dull red vial that smells faintly of herbs.", "heal": (10, 15)},
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


def generate_dungeon(num_rooms=8, depth=1, place_amulet=True):
    """
    Build a random dungeon as a graph of connected rooms.

    Uses a random walk over a grid of (x, y) coordinates so that compass
    directions stay consistent (going north then south always gets you
    back where you started), then layers in extra loop connections,
    monsters, items, and a goal room.

    `depth` shifts monster difficulty tier up on deeper floors. If
    `place_amulet` is True, the goal room holds the Ancient Amulet
    (win condition); otherwise it gets a staircase down to the next floor.

    Returns (entry_room, goal_room).
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

    depth_shift = (depth - 1) // 2  # deeper floors skew toward tougher tiers

    for room, room_dist in dist.items():
        if room is entry or room is goal_room:
            continue

        if random.random() < 0.6:
            base_tier = 1 if room_dist <= 1 else (2 if room_dist <= 3 else 3)
            tier = min(3, base_tier + depth_shift)
            candidates = [t for t in MONSTER_TEMPLATES if t["tier"] == tier] or MONSTER_TEMPLATES
            template = _weighted_choice(candidates)
            hp = random.randint(*template["hp"])
            atk_min, atk_max = template["atk"]
            room.monsters.append(Monster(template["name"], hp, atk_min, atk_max))

        if random.random() < 0.5:
            if random.random() < 0.5:
                wt = random.choice(WEAPON_TEMPLATES)
                damage_min, damage_max = wt["damage"]
                room.items.append(Weapon(
                    wt["name"], wt["description"], damage_min, damage_max,
                    wt.get("str_req", 0), wt.get("attack_bonus", 0),
                ))
            else:
                pt = random.choice(POTION_TEMPLATES)
                heal = random.randint(*pt["heal"])
                room.items.append(Potion(pt["name"], pt["description"], heal))

    if place_amulet:
        goal_room.items.append(Item(
            "Ancient Amulet",
            "A pulsing amulet radiating ancient power. This is what you came for."
        ))
    else:
        goal_room.stairs_down = True

    return entry, goal_room
