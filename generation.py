"""Procedural dungeon generation: content tables plus the random-walk
graph builder that lays out rooms, monsters, items, and the goal room."""

import random
from collections import deque

from entities import Monster
from items import Item, Weapon, Potion, Armor, Food
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
    {"name": "Giant Rat",      "hp": (6, 10),  "atk": (1, 3),  "tier": 1, "weight": 5, "xp": (2, 4),   "gold": (1, 3)},
    {"name": "Cave Spider",    "hp": (8, 12),  "atk": (2, 4),  "tier": 1, "weight": 4, "xp": (3, 5),   "gold": (2, 4)},
    {"name": "Skeleton",       "hp": (10, 16), "atk": (2, 5),  "tier": 1, "weight": 3, "xp": (4, 6),   "gold": (3, 5)},
    {"name": "Goblin Grunt",   "hp": (12, 18), "atk": (3, 6),  "tier": 2, "weight": 4, "xp": (6, 9),   "gold": (5, 8)},
    {"name": "Rot Zombie",     "hp": (16, 22), "atk": (3, 7),  "tier": 2, "weight": 3, "xp": (7, 10),  "gold": (6, 9)},
    {"name": "Crypt Wight",    "hp": (18, 24), "atk": (4, 8),  "tier": 2, "weight": 2, "xp": (8, 12),  "gold": (7, 11)},
    {"name": "Dungeon Ogre",   "hp": (25, 35), "atk": (5, 10), "tier": 3, "weight": 2, "xp": (14, 20), "gold": (12, 18)},
    {"name": "Shadow Wraith",  "hp": (20, 28), "atk": (6, 12), "tier": 3, "weight": 2, "xp": (12, 18), "gold": (10, 16)},
]

WEAPON_TEMPLATES = [
    #Tier 1 weapons
    {"name": "Dirk",            "description": "A simple, short blade.",                                        "damage": (2, 12), "str_req": 7},
    {"name": "Sword",           "description": "A well-balanced blade.",                                        "damage": (2, 15), "str_req": 7},
    {"name": "Hand Axe",        "description": "Most commonly used to fell trees.",                             "damage": (2, 14), "str_req": 7},
    {"name": "Quarterstaff",    "description": "A balanced wooden staff, tipped in iron.",                      "damage": (2, 12), "str_req": 8},
    {"name": "Spear",           "description": "A long polearm with a sharpened iron tip.",                     "damage": (2, 18), "str_req": 8},
    {"name": "Hunting Bow",     "description": "A simple ranged weapon for hunting game.",                      "damage": (2, 20), "str_req": 8},
    
    #Tier 2 weapons
    {"name": "Mace",            "description": "A wicked, spiked ball tops this cruel weapon.",                 "damage": (3, 22), "str_req": 10},
    {"name": "Scimitar",        "description": "A blade that cuts through the air with deadly grace.",          "damage": (3, 22), "str_req": 10},
    {"name": "Shield",          "description": "A sturdy barrier against incoming attacks.",                    "damage": (3, 20), "str_req": 11},
    {"name": "Axe",             "description": "A two-handed axe with a sharp edge.",                           "damage": (3, 24), "str_req": 11},
    {"name": "Halberd",         "description": "A polearm adorned with with a steel blade.",                    "damage": (3, 24), "str_req": 11},
    {"name": "Battle Hammer",   "description": "A  weapon designed for crushing bones and armor.",              "damage": (3, 26), "str_req": 12},
    {"name": "Long Bow",        "description": "A ranged weapon designed to pierce and maim.",                  "damage": (3, 28), "str_req": 12},
    {"name": "Stiletto",        "description": "A thin, needle-like blade.",                                    "damage": (3, 20), "str_req": 10},

    #Tier 3 weapons
    {"name": "Morningstar",     "description": "A spiked head tops the metal shaft of this instrument.",        "damage": (4, 25), "str_req": 14},
    {"name": "Long Sword",      "description": "A double-edged blade that cuts enemies with precision.",        "damage": (4, 25), "str_req": 14},
    {"name": "Crossbow",        "description": "A mechanical system that fires bolts with great force.",        "damage": (4, 34), "str_req": 15},
    {"name": "Repeating Bow",   "description": "A bow that can unleash a storm of arrows.",                     "damage": (4, 30), "str_req": 15},
    {"name": "Whip",            "description": "This deadly length of rope lashes with precision.",             "damage": (4, 24), "str_req": 13},
    {"name": "Hidden Blade",    "description": "A concealed blade tucked under the sleeve.",                    "damage": (4, 24), "str_req": 13},
    {"name": "Scythe",          "description": "A farming instrument turned deadly weapon.",                    "damage": (4, 32), "str_req": 15},

    #Tier 4 weapons
    {"name": "Battle Axe",      "description": "The enormous head of this weapon cuts down enemies with ease.", "damage": (5, 32), "str_req": 17},
    {"name": "Glaive",          "description": "The reach of this hefty weapon is unmatched.",                  "damage": (5, 38), "str_req": 17},
    {"name": "Greatsword",      "description": "This mighty blade strikes with tremendous force.",              "damage": (5, 30), "str_req": 17},
    {"name": "War Hammer",      "description": "This crushing lump of steel and lead pulverizes enemies.",      "damage": (5, 34), "str_req": 18},
    {"name": "Assassin's Blade","description": "This hidden dagger is favored by the shadows.",                 "damage": (5, 28), "str_req": 16},
    {"name": "Great Shield",    "description": "A towering mass of metal stops any attack.",                    "damage": (5, 28), "str_req": 18},
    {"name": "Recurve Bow",     "description": "This massive bow with curved limbs fires enormous bolts.",      "damage": (5, 40), "str_req": 18},

    #Tier 5 weapons
    {"name": "Zewihander",      "description": "More slab of metal than blade, this weapon is unstoppable.",            "damage": (7, 35), "str_req": 21},
    {"name": "War Maul",        "description": "A massive chunk of metal. Crushes anything in its path.",               "damage": (7, 40), "str_req": 21},
    {"name": "Greataxe",        "description": "Dual blades adorn this weapon of pure force.",                          "damage": (7, 38), "str_req": 21},
    {"name": "War Bow",         "description": "This instrument of ruin  fires bolts designed to destroy castles.",     "damage": (7, 45), "str_req": 21},

    #Tier 0 weapons
    {"name": "Wand",            "description": "A simple yew wand to channel magic.",                                   "damage": (1, 6), "str_req": 5},
    {"name": "Short Bow",       "description": "A simple bow designed for quick shots.",                                "damage": (1, 12), "str_req": 5},
    {"name": "Dagger",          "description": "A simple, short blade.",                                                "damage": (1, 8), "str_req": 5},
    {"name": "Short Sword",     "description": "A well-balanced blade.",                                                "damage": (1, 10), "str_req": 5} 


]

POTION_TEMPLATES = [
    {"name": "Healing Potion", "description": "A dull red vial that smells faintly of herbs.",    "kind": "heal",   "power": (10, 15)},
    {"name": "Vial of Acid",   "description": "A hissing green liquid, best thrown, not drunk.",   "kind": "damage", "power": (8, 14)},
]

ARMOR_TEMPLATES = [
    {"name": "Cloth Armor",   "description": "Simple woven robes, better than nothing.",                  "block": (0, 4),  "str_req": 5},
    {"name": "Leather Armor", "description": "Boiled leather plates stitched over a hide vest.",           "block": (1, 8),  "str_req": 8},
    {"name": "Mail Armor",    "description": "Interlocking iron rings form a flexible shirt.",              "block": (2, 12), "str_req": 11},
    {"name": "Scale Armor",   "description": "Overlapping metal scales riveted to a leather backing.",     "block": (3, 16), "str_req": 14},
    {"name": "Plate Armor",   "description": "A full suit of forged steel plate.",                         "block": (4, 20), "str_req": 18},
]

FOOD_TEMPLATES = [
    {"name": "Rations", "description": "Dried meat, hardtack, and a bit of salt.", "satiety": 100},
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
            xp = random.randint(*template["xp"])
            gold = random.randint(*template["gold"])
            room.monsters.append(Monster(template["name"], hp, atk_min, atk_max, XP=xp, GOLD=gold))

        if random.random() < 0.5:
            category = random.choice(["weapon", "potion", "armor", "food"])
            if category == "weapon":
                wt = random.choice(WEAPON_TEMPLATES)
                damage_min, damage_max = wt["damage"]
                room.items.append(Weapon(
                    wt["name"], wt["description"], damage_min, damage_max,
                    wt.get("str_req", 0), wt.get("attack_bonus", 0),
                ))
            elif category == "potion":
                pt = random.choice(POTION_TEMPLATES)
                power = pt["power"]
                if isinstance(power, tuple):
                    power = random.randint(*power)
                room.items.append(Potion(pt["name"], pt["description"], pt["kind"], power, pt.get("duration", 0)))
            elif category == "armor":
                at = random.choice(ARMOR_TEMPLATES)
                block_min, block_max = at["block"]
                room.items.append(Armor(
                    at["name"], at["description"], block_min, block_max,
                    at.get("str_req", 0),
                ))
            else:
                ft = random.choice(FOOD_TEMPLATES)
                room.items.append(Food(ft["name"], ft["description"], ft["satiety"]))

    if place_amulet:
        goal_room.items.append(Item(
            "Ancient Amulet",
            "A pulsing amulet radiating ancient power. This is what you came for."
        ))
    else:
        goal_room.stairs_down = True

    return entry, goal_room
