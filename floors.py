"""
Floor and act progression.

A "floor" is one generated room-graph (see generation.generate_dungeon),
tagged with a depth number. An "act" is a band of floors that can later
share a theme, monster set, or difficulty curve — for now it's just
depth // FLOORS_PER_ACT, but ROOM_THEMES/MONSTER_TEMPLATES could be
swapped out per-act here without touching anything else.

The hub room is a static, non-generated room the player starts in
before entering the dungeon proper.
"""

from generation import generate_dungeon
from world import Room

FLOORS_PER_ACT = 5
FINAL_FLOOR_DEPTH = 5   # the floor whose goal room holds the Ancient Amulet

BASE_ROOMS_PER_FLOOR = 8
ROOMS_PER_FLOOR_GROWTH = 2   # extra rooms added per floor of depth
MAX_ROOMS_PER_FLOOR = 20


def act_for_depth(depth):
    """Which act a given floor depth belongs to (1-indexed)."""
    return ((depth - 1) // FLOORS_PER_ACT) + 1


def is_final_floor(depth):
    return depth >= FINAL_FLOOR_DEPTH


def make_hub_room():
    """The player's starting room, above the dungeon entrance."""
    hub = Room(
        "Camp",
        "A small fire crackles at the mouth of the dungeon. Your gear is "
        "stacked against a nearby rock, and a dark passage leads down into "
        "the earth. Type 'enter' when you're ready to descend."
    )
    hub.coord = (0, 0)
    return hub


def generate_floor(depth):
    """
    Generate a single floor at the given depth.

    Returns (entry_room, goal_room). Deeper floors are somewhat larger
    and tougher (see generate_dungeon's depth_shift). The final floor's
    goal room holds the Ancient Amulet; every earlier floor's goal room
    gets a staircase down instead.
    """
    num_rooms = min(
        MAX_ROOMS_PER_FLOOR,
        BASE_ROOMS_PER_FLOOR + (depth - 1) * ROOMS_PER_FLOOR_GROWTH,
    )
    place_amulet = is_final_floor(depth)
    return generate_dungeon(num_rooms=num_rooms, depth=depth, place_amulet=place_amulet)
