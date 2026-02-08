"""Game state containers and shared state helpers."""

from __future__ import annotations

from dataclasses import dataclass, field
import random
from typing import Dict, Optional

from content.items import ITEMS


def _default_inventory() -> Dict[str, int]:
    return {
        "rusted_blade": 1,
        "patched_coat": 1,
        "minor_potion": 2,
        "sturdy_bandage": 1,
    }


def _default_equipment() -> Dict[str, Optional[str]]:
    return {
        "weapon": "rusted_blade",
        "armor": "patched_coat",
        "shield": None,
        "accessory": None,
        "aura": None,
    }


@dataclass
class Player:
    """All mutable player state."""

    name: str = "Wanderer"
    base_max_hp: int = 50
    base_attack: int = 8
    base_defense: int = 5
    hp: int = 50
    xp: int = 0
    level: int = 1
    skill_points: int = 0
    gold: int = 20
    inventory: Dict[str, int] = field(default_factory=_default_inventory)
    equipment: Dict[str, Optional[str]] = field(default_factory=_default_equipment)
    skills: set[str] = field(default_factory=set)
    cooldowns: Dict[str, int] = field(default_factory=dict)
    titles: list[str] = field(default_factory=list)
    temporary_bonuses: Dict[str, int] = field(default_factory=dict)


@dataclass
class Encounter:
    """Live encounter state."""

    enemy_id: str
    current_hp: int
    intent_index: int = 0
    player_defending: bool = False
    special_phase: str = "combat"
    witch_barrier_active: bool = False
    turn_count: int = 0


@dataclass
class GameState:
    """Single source of truth for game runtime."""

    player: Player
    current_location_id: str = "old_shack"
    quest_stage: str = "awakening"
    flags: set[str] = field(default_factory=set)
    active_encounter: Optional[Encounter] = None
    discovered_locations: set[str] = field(default_factory=set)
    turn_count: int = 0
    game_over: bool = False
    victory: bool = False
    rng: random.Random = field(default_factory=random.Random)


def create_initial_state() -> GameState:
    """Create a fresh game state for a new run."""
    state = GameState(player=Player())
    state.discovered_locations.add(state.current_location_id)
    return state


def get_effective_stats(player: Player) -> Dict[str, int]:
    """Return effective combat stats after gear and temporary bonuses."""
    attack = player.base_attack
    defense = player.base_defense
    max_hp = player.base_max_hp

    for item_id in player.equipment.values():
        if not item_id:
            continue
        item = ITEMS.get(item_id, {})
        attack += int(item.get("attack_bonus", 0))
        defense += int(item.get("defense_bonus", 0))
        max_hp += int(item.get("max_hp_bonus", 0))

    attack += int(player.temporary_bonuses.get("attack", 0))
    defense += int(player.temporary_bonuses.get("defense", 0))
    max_hp += int(player.temporary_bonuses.get("max_hp", 0))

    return {
        "max_hp": max(1, max_hp),
        "attack": max(1, attack),
        "defense": max(0, defense),
    }


def clamp_player_hp(player: Player) -> None:
    """Clamp hp to [0, effective_max_hp]."""
    max_hp = get_effective_stats(player)["max_hp"]
    player.hp = max(0, min(player.hp, max_hp))


def heal_player(player: Player, amount: int) -> int:
    """Heal and return amount restored."""
    before = player.hp
    player.hp += max(0, amount)
    clamp_player_hp(player)
    return player.hp - before


def add_item(player: Player, item_id: str, qty: int = 1) -> None:
    """Add item(s) to inventory."""
    if qty <= 0:
        return
    player.inventory[item_id] = player.inventory.get(item_id, 0) + qty


def remove_item(player: Player, item_id: str, qty: int = 1) -> bool:
    """Remove item(s) if possible."""
    if qty <= 0:
        return True
    owned = player.inventory.get(item_id, 0)
    if owned < qty:
        return False
    remaining = owned - qty
    if remaining <= 0:
        player.inventory.pop(item_id, None)
    else:
        player.inventory[item_id] = remaining
    return True


def has_item(player: Player, item_id: str, qty: int = 1) -> bool:
    """Check whether player has at least qty of item."""
    return player.inventory.get(item_id, 0) >= qty


def xp_to_next_level(level: int) -> int:
    """Growth curve for level progression."""
    return 40 + max(0, level - 1) * 30


def award_xp(player: Player, amount: int) -> list[str]:
    """Grant xp and level up as needed, returning messages."""
    messages: list[str] = []
    if amount <= 0:
        return messages

    player.xp += amount
    messages.append(f"You gain {amount} XP.")

    while player.xp >= xp_to_next_level(player.level):
        threshold = xp_to_next_level(player.level)
        player.xp -= threshold
        player.level += 1
        player.base_max_hp += 6
        player.base_attack += 1
        player.base_defense += 1
        clamp_player_hp(player)
        player.hp = get_effective_stats(player)["max_hp"]
        messages.append(
            f"Level up! You are now level {player.level}. Base stats increased and HP fully restored."
        )

    return messages


def normalize_name(text: str) -> str:
    """Normalize text for command matching."""
    return "".join(ch for ch in text.lower().strip() if ch.isalnum() or ch.isspace())


def find_item_id_by_query(player: Player, query: str) -> Optional[str]:
    """Find an owned item by id or fuzzy name."""
    query_norm = normalize_name(query)
    if not query_norm:
        return None

    if query in player.inventory:
        return query

    if query_norm in player.inventory:
        return query_norm

    for item_id in player.inventory:
        item_name = ITEMS.get(item_id, {}).get("name", item_id)
        if normalize_name(item_name) == query_norm:
            return item_id
        if query_norm in normalize_name(item_name):
            return item_id

    return None

