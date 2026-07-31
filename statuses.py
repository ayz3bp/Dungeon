"""
Skeleton status-effect system shared by Player and Monster.

Both entities carry a `statuses` dict: {name: {"turns": remaining, ...}}.
`turns` counts down once per whole turn elapsed — the same turn-boundary
cadence GameState._process_world_turns already fires monster attacks on
(see world.py) — and the status is removed once it hits zero. Anything
a status needs beyond "is this active" / "how long is left" (a flat stat
bonus that must be reversed on expiry, a per-turn damage tick, a
multi-step schedule) is stored as extra keys on that status's dict and
interpreted by name in tick_statuses below.

This is deliberately thin — enough to drive the potions in items.py /
generation.py, not a full effect-resolution engine. Wiring a status into
an actual mechanic beyond "it exists and counts down" means checking
has_status(entity, "name") at the specific place it should matter — see
GameState._process_world_turns (stun/slow) and Player.attack (true_sight)
in world.py/entities.py for the pattern to follow when adding another.
"""

import math

# Statuses that Potion of Purity's immunity blocks from being newly
# applied. Refreshing/re-icking an *existing* one of these is unaffected —
# this only stops a fresh application while immune.
HARMFUL_STATUSES = {"slow", "burning", "stun", "toxic"}


def has_status(entity, name):
    """True if `entity` currently has status `name` active."""
    statuses = getattr(entity, "statuses", None)
    return bool(statuses) and name in statuses


def apply_status(entity, name, turns, **extra):
    """
    Add status `name` to `entity` for `turns` (whole turns). If it's
    already active, refreshing takes the longer of the two remaining
    durations and updates any extra data (rather than stacking a second
    copy). Returns False without applying anything if `name` is a
    harmful status and `entity` currently has Potion of Purity's
    'purity' status active; True otherwise.
    """
    if not hasattr(entity, "statuses"):
        entity.statuses = {}
    if name in HARMFUL_STATUSES and has_status(entity, "purity"):
        return False

    existing = entity.statuses.get(name)
    if existing:
        existing["turns"] = max(existing["turns"], turns)
        existing.update(extra)
    else:
        entity.statuses[name] = {"turns": turns, **extra}
    return True


def tick_statuses(entity, count, on_message=None):
    """
    Advance every status on `entity` by `count` whole turns. A few kinds
    do something every tick on their own (damage-over-time for
    burning/toxic, the Healing Potion's staggered schedule); everything
    else just counts down and is removed at zero. `on_message`, if given,
    is called once per message produced (the caller decides whether/how
    to print it — see GameState._process_world_turns).
    """
    statuses = getattr(entity, "statuses", None)
    if not statuses:
        return

    def emit(message):
        if on_message:
            on_message(message)

    for name in list(statuses.keys()):
        data = statuses[name]

        if name == "healing_potion":
            schedule = data.get("schedule", [])
            for _ in range(count):
                if not schedule:
                    break
                fraction = schedule.pop(0)
                if entity.alive:
                    before = entity.hp
                    healed = math.ceil(entity.max_hp * fraction)
                    entity.hp = min(entity.max_hp, entity.hp + healed)
                    emit(
                        f"The healing potion continues to work, restoring "
                        f"{entity.hp - before} HP. ({entity.hp}/{entity.max_hp} HP)"
                    )
            if not schedule:
                del statuses[name]
            continue

        if name in ("burning", "toxic") and entity.alive:
            dmg = data.get("power", 0) * count
            if dmg:
                entity.hp = max(0, entity.hp - dmg)
                emit(f"{name.capitalize()} deals {dmg} damage. ({entity.hp}/{entity.max_hp} HP)")

        data["turns"] -= count
        if data["turns"] <= 0:
            if name == "purity" and "res_bonus" in data:
                entity.RES -= data["res_bonus"]
            elif name == "rejuvenation":
                entity.REG -= data.get("reg_bonus", 0)
                entity.MPG -= data.get("mpg_bonus", 0)
            del statuses[name]
            emit(f"Your {name.replace('_', ' ')} fades.")


def describe_statuses(entity):
    """One-line summary of active statuses and their remaining turns, or
    None if there aren't any — used by the 'status' command."""
    statuses = getattr(entity, "statuses", None)
    if not statuses:
        return None
    parts = [f"{name} ({data['turns']})" for name, data in statuses.items()]
    return ", ".join(parts)
