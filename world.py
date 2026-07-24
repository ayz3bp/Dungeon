"""The dungeon's world model: Room layout/state and the live GameState
that tracks the player's position, combat, inventory, and minimap."""

import math
import random

from items import Weapon, Potion, Armor, Food

# Turn costs for player actions. Every action that takes in-game time
# should go through GameState.advance_turns() with one of these (or a
# future weapon/spell-specific cost) so hunger and regen stay in sync
# with everything else.
MOVE_TURN_COST = 2      # moving/fleeing/using stairs between rooms
ATTACK_TURN_COST = 0.5  # a single attack with a base weapon
EXPLORE_TURN_COST = 1   # searching the current room for more loot/enemies


def _apply_potion_effect(potion, entity):
    """
    Apply a potion's effect to `entity` — self.player when drunk, or a
    Monster when thrown — and return a short description of what
    happened, for the caller to fold into its own message.

    To add a new potion kind, add a branch here. If a kind only makes
    sense for one side (e.g. a future stat buff Monster doesn't carry),
    guard it with hasattr(entity, ...) the way world.py already does
    elsewhere, rather than assuming the target is always the player.
    """
    if potion.kind == "heal":
        before = entity.hp
        entity.hp = min(entity.max_hp, entity.hp + potion.power)
        return f"restores {entity.hp - before} HP ({entity.hp}/{entity.max_hp} HP)"
    elif potion.kind == "damage":
        entity.hp = max(0, entity.hp - potion.power)
        return f"deals {potion.power} damage ({entity.hp}/{entity.max_hp} HP)"
    else:
        return "has no effect"


class Room:
    # Flavor label shown for each size, and how many extra descriptions
    # a bigger room supports (see explore() in GameState below): a size-1
    # room dries up after 1 explore, a size-4 room after 4.
    SIZE_LABELS = {1: "Cramped", 2: "Modest", 3: "Spacious", 4: "Grand"}

    def __init__(self, name, description):
        self.name = name
        self.description = description
        self.exits = {}      # direction (str) -> Room
        self.monsters = []
        self.items = []
        self.coord = None    # (x, y) grid position, set during generation
        self.stairs_down = False  # True on a floor's goal room, unless it holds the Amulet
        self.stairs_up = False    # True on a floor's entry room, except floor 1 (camp doesn't count)
        self.next_floor_entry = None  # cached entry room of the floor below, once generated

        # Exploration state (see generation.py for how these get set, and
        # GameState.explore() for how they're used).
        self.size = 1               # 1-4, how much this room supports exploring
        self.room_type = "normal"   # "normal" or "puzzle"
        self.puzzle_kind = None     # flavor text naming the puzzle, if any
        self.puzzle_solved = False  # only meaningful for room_type == "puzzle"
        self.explore_progress = 0   # times explored (normal) / progress made (puzzle)

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
        size_label = self.SIZE_LABELS.get(self.size)
        header = f"== {self.name} ({size_label}) ==" if size_label else f"== {self.name} =="
        lines = [header, self.description]
        if self.exits:
            exit_list = ", ".join(sorted(self.exits.keys()))
            lines.append(f"Exits: {exit_list}")
        living = [m for m in self.monsters if m.alive]
        if living:
            lines.append(
                "You see: " + ", ".join(f"{m.name} ({m.hp}/{m.max_hp} HP)" for m in living)
            )
        if self.items:
            lines.append("Items here: " + ", ".join(i.name for i in self.items))
        if self.room_type == "puzzle" and not self.puzzle_solved:
            lines.append(f"You notice {self.puzzle_kind} here. (try 'explore')")
        elif self.room_type == "normal" and self.explore_progress < self.size:
            lines.append("This room looks like it might reward a closer look. (try 'explore')")
        if self.stairs_down:
            lines.append("A stairway leads down into darkness. (type 'descend' to continue)")
        if self.stairs_up:
            lines.append("A stairway leads back up to the previous floor. (type 'ascend' to go back)")
        return "\n".join(lines)


class GameState:
    def __init__(self, starting_room, player):
        self.current_room = starting_room
        self.player = player
        self.turn_count = 0
        self.running = True
        self.visited = {starting_room}
        self.in_dungeon = False
        self.depth = 0
        self.act = 1
        self.floor_stack = []  # (room, depth, act, visited) to return to on ascend
        self.floor_visited_cache = {}  # entry_room -> visited set, saved whenever we leave that floor

    def advance_turns(self, amount):
        """
        Advance the turn counter by `amount` turns (fractional turns are
        fine, e.g. an attack costing half a turn). This is the single
        place turn-based effects tick: hunger drain/penalties/wasting
        damage, and passive HP/MP regen — and the single place that
        checks whether the player has died, whatever the cause.

        It's also the single place the world reacts to the player. The
        player only spends turns by acting, so this is where "an enemy
        acts after each turn" gets enforced: every time this call pushes
        turn_count across a whole-number boundary, every living monster
        in the current room gets one attack. A cheap action (0.5-turn
        attack) only crosses a boundary every other swing — two attacks
        add up to one turn's worth of monster response — while a costly
        action (a 2-turn move) crosses two boundaries at once, so an
        enemy left standing gets two attacks for it.
        """
        old_turn_count = self.turn_count
        self.turn_count += amount

        for message in self.player.tick_hunger(amount):
            print(message)

        if self.player.alive:
            self.player.tick_regen(amount)

        turns_elapsed = math.floor(self.turn_count) - math.floor(old_turn_count)
        if turns_elapsed > 0 and self.running and self.player.alive:
            self._monster_turn(turns_elapsed)

        if self.running and not self.player.alive:
            print("\nYou have died. Game over.")
            self.running = False

    def _monster_turn(self, count):
        """
        Let every living monster in the current room attack once, `count`
        times over (once per whole turn the triggering action crossed).
        Right now fights are always single-enemy, but this already loops
        over every living monster in the room so a multi-monster room
        (or a monster gaining an extra attack) works without changes here.
        """
        for _ in range(count):
            if not self.player.alive:
                break
            for monster in self.current_room.monsters:
                if not monster.alive:
                    continue
                if not self.player.alive:
                    break
                retaliation = monster.attack()
                block = self.player.block()
                damage_taken = max(0, retaliation - block)
                self.player.hp = max(0, self.player.hp - damage_taken)
                print(
                    f"The {monster.name} claws back for {damage_taken} damage. "
                    f"({self.player.hp}/{self.player.max_hp} HP)"
                )

    def enter_dungeon(self):
        """Leave the hub and generate floor 1. Only valid from the hub."""
        if self.in_dungeon:
            print("You're already in the dungeon.")
            return
        import floors
        entry_room, _goal_room = floors.generate_floor(depth=1)
        self.current_room = entry_room
        self.visited = {entry_room}
        self.in_dungeon = True
        self.depth = 1
        self.act = floors.act_for_depth(self.depth)
        print("You step into the darkness and the passage seals behind you...\n")
        self.advance_turns(MOVE_TURN_COST)
        if self.running:
            print(self.current_room.describe())

    def descend(self):
        """Generate the next floor down from a room with stairs_down set."""
        if not self.in_dungeon:
            print("There's nothing to descend here.")
            return
        if not self.current_room.stairs_down:
            print("There are no stairs down here.")
            return

        import floors
        next_depth = self.depth + 1

        if self.current_room.next_floor_entry is not None:
            # We've been down these stairs before — reuse the exact same floor
            # (monsters/items/state as we left it) instead of regenerating it.
            entry_room = self.current_room.next_floor_entry
            restored_visited = self.floor_visited_cache.get(entry_room, {entry_room})
        else:
            entry_room, _goal_room = floors.generate_floor(depth=next_depth)
            entry_room.stairs_up = True
            self.current_room.next_floor_entry = entry_room
            restored_visited = {entry_room}

        # Leaving costs the turns, so anything still alive in this room gets
        # its attacks in now, before you're gone — arriving downstairs doesn't
        # trigger anything on its own.
        self.advance_turns(MOVE_TURN_COST)
        if not self.running:
            return

        self.floor_stack.append((self.current_room, self.depth, self.act, self.visited))

        self.current_room = entry_room
        self.visited = restored_visited
        self.depth = next_depth
        new_act = floors.act_for_depth(self.depth)
        if new_act != self.act:
            print(f"\nYou feel the nature of the dungeon shift as you descend... (Act {new_act})")
        self.act = new_act
        print(f"You descend to depth {self.depth}.\n")
        print(self.current_room.describe())

    def ascend(self):
        """Return to the previous floor's stairs-down room, exactly as you left it."""
        if not self.in_dungeon:
            print("There's nothing to ascend to.")
            return
        if not self.current_room.stairs_up:
            print("There are no stairs up here.")
            return
        if not self.floor_stack:
            # Floor 1's entry has no stairs_up set, so this shouldn't normally
            # trigger — but guard anyway rather than returning to camp.
            print("This passage seems to lead nowhere. Best not to risk it.")
            return

        # Leaving costs the turns, so anything still alive in this room gets
        # its attacks in now, before you're gone — arriving upstairs doesn't
        # trigger anything on its own.
        self.advance_turns(MOVE_TURN_COST)
        if not self.running:
            return

        # Save this floor's progress so descending these same stairs again
        # later brings you right back to where you left off.
        self.floor_visited_cache[self.current_room] = self.visited

        prev_room, prev_depth, prev_act, prev_visited = self.floor_stack.pop()
        self.current_room = prev_room
        self.visited = prev_visited
        self.depth = prev_depth
        self.act = prev_act
        print(f"You climb back up to depth {self.depth}.\n")
        print(self.current_room.describe())

    def move(self, direction):
        if direction not in self.current_room.exits:
            print("You can't go that way.")
            return

        destination = self.current_room.exits[direction]

        # Leaving costs the turns, so anything still alive in this room gets
        # its attacks in now, before you're gone — walking into the new room
        # doesn't trigger anything on its own.
        self.advance_turns(MOVE_TURN_COST)
        if not self.running:
            return

        self.current_room = destination
        self.visited.add(self.current_room)
        print(self.current_room.describe())

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
            print(f"You gain {target.XP} XP and {target.GOLD} gold.")
            levels_gained = self.player.gain_xp(target.XP)
            self.player.gold += target.GOLD
            for level in levels_gained:
                print(
                    f"\n*** Level up! You are now level {level}. ***\n"
                    f"You gain a stat point (use 'level <stat>' to spend it) "
                    f"and recover a bit of HP/MP."
                )

        # Monster retaliation (if the target or any other monster here
        # survived) now happens inside advance_turns, once a full turn's
        # worth of action has actually elapsed — see _monster_turn.
        self.advance_turns(ATTACK_TURN_COST)

    def flee(self, direction):
        """Attempt to escape combat by moving to another room."""
        if direction not in self.current_room.exits:
            print("You can't flee that way.")
            return

        destination = self.current_room.exits[direction]
        print(f"You break away and flee {direction}!")

        # Leaving costs the turns, so anything still alive in this room gets
        # its attacks in now, before you're gone.
        self.advance_turns(MOVE_TURN_COST)
        if not self.running:
            return

        self.current_room = destination
        self.visited.add(self.current_room)
        print(self.current_room.describe())

    def explore(self):
        """
        Search the current room for more than what's visible at a glance.
        Costs 1 turn either way.

        Puzzle rooms: each explore makes progress; once progress reaches
        the room's size, the puzzle is solved and pays out a reward.
        Normal rooms: each explore has a chance to turn up an item, spring
        an ambush, or find nothing — up to `size` times, after which the
        room is tapped out.
        """
        if not self.in_dungeon:
            print("There's nothing to explore here.")
            return

        room = self.current_room
        import generation  # local import: generation.py imports from this module

        if room.room_type == "puzzle":
            if room.puzzle_solved:
                print(f"{room.puzzle_kind[0].upper()}{room.puzzle_kind[1:]} here has already given up its secrets.")
                self.advance_turns(EXPLORE_TURN_COST)
                return

            room.explore_progress += 1
            if room.explore_progress >= room.size:
                room.puzzle_solved = True
                reward = generation.roll_explore_loot()
                room.items.append(reward)
                gold = random.randint(5, 10) * self.depth
                self.player.gold += gold
                print(
                    f"With one final effort, {room.puzzle_kind} gives way! "
                    f"A hidden cache opens, revealing a {reward.name} and {gold} gold."
                )
            else:
                print(
                    f"You work at {room.puzzle_kind}. It feels close to giving way. "
                    f"({room.explore_progress}/{room.size})"
                )
            self.advance_turns(EXPLORE_TURN_COST)
            return

        if room.explore_progress >= room.size:
            print("You've thoroughly searched this room. There's nothing more to find.")
            self.advance_turns(EXPLORE_TURN_COST)
            return

        room.explore_progress += 1
        roll = random.random()
        if roll < 0.15:
            monster = generation.roll_ambush_monster(self.depth)
            room.monsters.append(monster)
            print(f"As you search, a {monster.name} lunges out at you!")
        elif roll < 0.65:
            item = generation.roll_explore_loot()
            room.items.append(item)
            print(f"Searching the room, you turn up a {item.name}.")
        else:
            print("You search the room but find nothing further of note.")

        self.advance_turns(EXPLORE_TURN_COST)

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
                if room.stairs_down:
                    return "D"
                if room.stairs_up:
                    return "U"
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
        legend = (
            "@ = you   o = visited   ? = known passage, unexplored\n"
            "D = stairs down   U = stairs up"
        )
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
        elif self.player.equipped_armor is item:
            self.player.equipped_armor = None
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
            self.drink(name_fragment)
        elif isinstance(item, Weapon):
            unmet = item.unmet_requirements(self.player)
            if unmet:
                reqs = ", ".join(
                    f"{stat} {required} (you have {getattr(self.player, stat, 0)})"
                    for stat, required in unmet.items()
                )
                print(f"You need {reqs} to wield the {item.name}.")
                return
            self.player.equipped_weapon = item
            low, high = self.player.damage_range
            print(
                f"You equip the {item.name} ({item.damage_min}-{item.damage_max} base damage)"
            )
        elif isinstance(item, Armor):
            unmet = item.unmet_requirements(self.player)
            if unmet:
                reqs = ", ".join(
                    f"{stat} {required} (you have {getattr(self.player, stat, 0)})"
                    for stat, required in unmet.items()
                )
                print(f"You need {reqs} to wear the {item.name}.")
                return
            self.player.equipped_armor = item
            low, high = self.player.block_range
            print(
                f"You equip the {item.name} ({item.block_min}-{item.block_max} base block) "
            )
        elif isinstance(item, Food):
            for message in self.player.eat(item.name, item.satiety_restore):
                print(message)
            self.player.inventory.remove(item)
        else:
            print(f"You can't figure out how to use the {item.name}.")

    def drink(self, name_fragment):
        """Drink a potion yourself — the effect applies to the player."""
        if not name_fragment:
            print("Drink what?")
            return
        item = self.find_item_in_inventory(name_fragment)
        if item is None:
            print(f"You aren't carrying a '{name_fragment}'.")
            return
        if not isinstance(item, Potion):
            print(f"You can't drink the {item.name}.")
            return

        effect = _apply_potion_effect(item, self.player)
        print(f"You drink the {item.name}. It {effect}.")
        self.player.inventory.remove(item)
        self.advance_turns(ATTACK_TURN_COST)

    def throw(self, name_fragment, target_name):
        """Throw a potion at a monster in the room — the effect applies to it."""
        if not name_fragment:
            print("Throw what?")
            return
        item = self.find_item_in_inventory(name_fragment)
        if item is None:
            print(f"You aren't carrying a '{name_fragment}'.")
            return
        if not isinstance(item, Potion):
            print(f"The {item.name} doesn't do much when thrown.")
            return

        if not target_name:
            living = [m for m in self.current_room.monsters if m.alive]
            if not living:
                print("There's nothing here to throw it at.")
                return
            target = living[0]
        else:
            target = self.find_monster(target_name)
            if target is None:
                print(f"There's no '{target_name}' here to throw it at.")
                return

        effect = _apply_potion_effect(item, target)
        print(f"You throw the {item.name} at the {target.name}. It {effect}.")
        self.player.inventory.remove(item)

        if not target.alive:
            print(f"The {target.name} collapses!")
            print(f"You gain {target.XP} XP and {target.GOLD} gold.")
            levels_gained = self.player.gain_xp(target.XP)
            self.player.gold += target.GOLD
            for level in levels_gained:
                print(
                    f"\n*** Level up! You are now level {level}. ***\n"
                    f"You have gained 2 stat points (use 'level <stat>' to spend it) "
                    f"and recover a bit of HP/MP."
                )

        self.advance_turns(ATTACK_TURN_COST)
