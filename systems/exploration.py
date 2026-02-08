"""Exploration, movement, and NPC interaction system."""

from __future__ import annotations

from typing import List, Optional

from content.world import LOCATIONS, NPCS
from game.state import GameState
from systems import combat
from systems.loot import ensure_core_skills


DIRECTION_ALIASES = {
    "n": "north",
    "s": "south",
    "e": "east",
    "w": "west",
    "u": "up",
    "d": "down",
}


def _location(state: GameState) -> dict:
    return LOCATIONS[state.current_location_id]


def _describe_location(state: GameState) -> str:
    location = _location(state)
    descriptions = location.get("descriptions", [])
    if not descriptions:
        return "You stand in a quiet place."
    return descriptions[state.turn_count % len(descriptions)]


def _npc_names_for_location(location_id: str, state: GameState) -> List[str]:
    names: List[str] = []
    for npc_id in LOCATIONS[location_id].get("npcs", []):
        if npc_id == "elle" and "onyx_witch_defeated" not in state.flags:
            continue
        names.append(NPCS.get(npc_id, {}).get("name", npc_id))
    return names


def look(state: GameState) -> List[str]:
    """Return a full location look message."""
    location = _location(state)
    exits = ", ".join(sorted(location.get("exits", {}).keys())) or "none"
    messages = [
        f"{location['name']} [{location['area']}]",
        _describe_location(state),
        f"Exits: {exits}",
    ]
    npc_names = _npc_names_for_location(state.current_location_id, state)
    if npc_names:
        messages.append(f"NPCs here: {', '.join(npc_names)}")
    return messages


def sense(state: GameState) -> List[str]:
    """Return hint text for current area."""
    location = _location(state)
    messages = [location.get("sense_hint", "Nothing unusual stands out.")]

    if state.current_location_id == "old_shack" and "met_old_man" not in state.flags:
        messages.append("A patient voice waits inside. Maybe you should talk first.")
    if state.current_location_id == "mountain_peak" and "dragon_defeated" not in state.flags:
        messages.append("The air tastes like ash and blood.")
    if state.current_location_id == "desolate_road" and "goblin_army_defeated" not in state.flags:
        messages.append("Small eyes track you from the broken walls.")
    if state.current_location_id == "witch_terrace" and "onyx_witch_defeated" not in state.flags:
        messages.append("A curse crawls over your skin with every breath.")
    if state.current_location_id == "witch_terrace" and "onyx_witch_defeated" in state.flags:
        if "elle_freed" not in state.flags:
            messages.append("A chain lock clicks faintly near Elle.")
    return messages


def _check_exit_requirement(state: GameState, requirement: dict) -> bool:
    all_flags = requirement.get("all_flags", [])
    any_flags = requirement.get("any_flags", [])
    if all_flags and any(flag not in state.flags for flag in all_flags):
        return False
    if any_flags and all(flag not in state.flags for flag in any_flags):
        return False
    return True


def _maybe_spawn_random_encounter(state: GameState) -> List[str]:
    location = _location(state)
    if state.active_encounter:
        return []
    chance = float(location.get("encounter_chance", 0.0))
    encounters = location.get("encounters", [])
    if chance <= 0 or not encounters:
        return []
    if state.rng.random() >= chance:
        return []

    total = sum(weight for _, weight in encounters)
    roll = state.rng.randint(1, total)
    cursor = 0
    selected_enemy = encounters[0][0]
    for enemy_id, weight in encounters:
        cursor += weight
        if roll <= cursor:
            selected_enemy = enemy_id
            break
    return combat.start_encounter(state, selected_enemy)


def _requirements_met(state: GameState, location: dict) -> bool:
    req_flags = location.get("boss_require_flags", [])
    return all(flag in state.flags for flag in req_flags)


def _handle_entry_events(state: GameState) -> List[str]:
    messages: List[str] = []
    location = _location(state)

    if state.current_location_id == "black_hall" and "makor_defeated" not in state.flags:
        if "black_hall_cutscene_seen" not in state.flags:
            state.flags.add("black_hall_cutscene_seen")
            messages.append("A voice booms from the dark hall: \"I have heard of you... from Elle.\"")
            messages.append("Your vision turns black.")
            state.current_location_id = "dungeon"
            state.discovered_locations.add("dungeon")
            messages.append("You wake in the dungeon beneath the hall.")
            messages.extend(combat.start_encounter(state, "king_makor"))
            return messages

    boss_id = location.get("boss_id")
    boss_flag = location.get("boss_flag")
    if boss_id and boss_flag not in state.flags and _requirements_met(state, location):
        messages.extend(combat.start_encounter(state, boss_id))
        return messages

    messages.extend(_maybe_spawn_random_encounter(state))
    return messages


def move(state: GameState, direction: str) -> List[str]:
    """Move to an adjacent location if possible."""
    if state.active_encounter:
        return ["You cannot move while an encounter is active."]

    direction = direction.lower().strip()
    direction = DIRECTION_ALIASES.get(direction, direction)

    location = _location(state)
    exits = location.get("exits", {})
    if direction not in exits:
        return [f"You cannot move {direction} from here."]

    requirements = location.get("exit_requirements", {}).get(direction)
    if requirements and not _check_exit_requirement(state, requirements):
        return [requirements.get("message", "That path is blocked for now.")]

    state.current_location_id = exits[direction]
    state.turn_count += 1
    state.discovered_locations.add(state.current_location_id)

    messages = [f"You move {direction}.", *look(state)]
    messages.extend(_handle_entry_events(state))
    return messages


def _npc_id_from_query(state: GameState, query: str) -> Optional[str]:
    query = query.lower().strip()
    location = _location(state)
    for npc_id in location.get("npcs", []):
        npc = NPCS.get(npc_id, {})
        if npc_id == "elle" and "onyx_witch_defeated" not in state.flags:
            continue
        if query in {npc_id, npc.get("name", "").lower()}:
            return npc_id
        if query and query in npc.get("name", "").lower():
            return npc_id
    return None


def talk(state: GameState, npc_query: str) -> List[str]:
    """Handle NPC dialogue and story triggers."""
    if state.active_encounter:
        return ["You cannot talk while fighting."]

    npc_id = _npc_id_from_query(state, npc_query)
    if not npc_id:
        return [f"No one named '{npc_query}' is here."]

    npc = NPCS[npc_id]
    messages: List[str] = []

    if npc_id == "wise_old_man":
        if "met_old_man" not in state.flags:
            state.flags.add("met_old_man")
            ensure_core_skills(state)
            messages.extend(npc.get("first_dialogue", []))
        else:
            lines = npc.get("repeat_dialogue", [])
            messages.append(lines[state.turn_count % len(lines)])
        if "hoard_treasure" in state.player.inventory and "hoard_delivered" not in state.flags:
            messages.append("\"If that hoard is truly from the cave, hand it here with `use hoard`.\"")
        return messages

    if npc_id == "elle":
        if "elle_freed" not in state.flags:
            return ["Elle is still bound. You need a key."]
        if "elle_met" not in state.flags:
            state.flags.add("elle_met")
            messages.extend(npc.get("first_dialogue", []))
            if "elle_cleansed" not in state.flags:
                messages.append("\"Something dark is still inside me. The vial might help.\"")
            return messages
        if "elle_cleansed" in state.flags:
            messages.extend(npc.get("cleansed_dialogue", []))
        else:
            lines = npc.get("repeat_dialogue", [])
            messages.append(lines[state.turn_count % len(lines)])
        return messages

    return ["They have nothing to say."]

