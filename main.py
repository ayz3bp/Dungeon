"""
Text-based ASCII dungeon crawler - entry point.
Find the Ancient Amulet buried somewhere in a randomly generated dungeon.
"""

import random
import sys

from character_creation import create_character
from floors import make_hub_room
from world import GameState
from commands import HELP_TEXT, parse_command, handle_command


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
    print("Find the Ancient Amulet buried deep below.")
    print(HELP_TEXT)

    player = create_character()

    hub_room = make_hub_room()
    state = GameState(hub_room, player)
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
