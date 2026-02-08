"""Loot, inventory, equipment, and training systems."""

from __future__ import annotations

from typing import List, Optional, Tuple

from content.enemies import ENEMIES, RARITY_TABLES
from content.items import EQUIPMENT_SLOT_BY_TYPE, ITEMS
from content.world import LOCATIONS
from game.state import (
    GameState,
    add_item,
    award_xp,
    clamp_player_hp,
    find_item_id_by_query,
    has_item,
    heal_player,
    remove_item,
)


def _weighted_pick(rng, weighted_items: list[tuple[str, int]]) -> Optional[str]:
    if not weighted_items:
        return None
    total = sum(max(0, weight) for _, weight in weighted_items)
    if total <= 0:
        return None
    roll = rng.randint(1, total)
    cursor = 0
    for item_id, weight in weighted_items:
        cursor += max(0, weight)
        if roll <= cursor:
            return item_id
    return weighted_items[-1][0]


def _item_name(item_id: str) -> str:
    return ITEMS.get(item_id, {}).get("name", item_id)


def _item_power_tuple(item_id: Optional[str]) -> tuple[float, int, int, int, int]:
    """Comparable combat value tuple for best-in-slot selection."""
    if not item_id:
        return (-9999.0, -9999, -9999, -9999, -9999)
    item = ITEMS.get(item_id, {})
    attack = int(item.get("attack_bonus", 0))
    defense = int(item.get("defense_bonus", 0))
    max_hp = int(item.get("max_hp_bonus", 0))
    value = int(item.get("value", 0))
    # Normalize HP into "stat points" using the same 3 HP ~= 1 training point convention.
    normalized = attack + defense + (max_hp / 3.0)
    return (normalized, attack, defense, max_hp, value)


def grant_rewards(state: GameState, enemy_id: str) -> List[str]:
    """Grant xp, gold, skill points, and drops for a defeated enemy."""
    enemy = ENEMIES[enemy_id]
    location = LOCATIONS.get(state.current_location_id, {})
    messages: List[str] = []

    messages.extend(award_xp(state.player, int(enemy.get("xp_reward", 0))))

    gold_reward = int(enemy.get("gold_reward", 0))
    if gold_reward:
        state.player.gold += gold_reward
        messages.append(f"You gain {gold_reward} gold.")

    skill_reward = int(enemy.get("skill_points_reward", 0))
    if enemy.get("category") == "normal":
        skill_reward += int(location.get("skill_points_per_kill", 0))
    if skill_reward:
        state.player.skill_points += skill_reward
        messages.append(f"You gain {skill_reward} skill points.")

    drops: List[str] = list(enemy.get("guaranteed_drops", []))

    loot_table = enemy.get("loot_table", [])
    drop_chance = 0.45 if enemy.get("category") == "normal" else 0.7
    if loot_table and state.rng.random() < drop_chance:
        rolled = _weighted_pick(state.rng, loot_table)
        if rolled:
            drops.append(rolled)

    if enemy.get("category") == "normal" and state.rng.random() < 0.04:
        rare_roll = _weighted_pick(state.rng, RARITY_TABLES["common_field"])
        if rare_roll:
            drops.append(rare_roll)

    seen = set()
    for item_id in drops:
        if item_id in seen:
            continue
        seen.add(item_id)
        item = ITEMS.get(item_id, {})
        if item.get("type") == "boon":
            bonus = int(item.get("skill_points_bonus", 0))
            if bonus:
                state.player.skill_points += bonus
                messages.append(f"Rare boon found: {_item_name(item_id)} grants {bonus} skill points.")
            continue
        add_item(state.player, item_id, 1)
        messages.append(f"Loot obtained: {_item_name(item_id)}.")

    return messages


def equip_item(state: GameState, item_query: str) -> List[str]:
    """Equip an owned item into its slot."""
    item_id = find_item_id_by_query(state.player, item_query)
    if not item_id:
        return [f"You do not have '{item_query}'."]

    item = ITEMS.get(item_id)
    if not item:
        return ["That item cannot be equipped."]

    slot = EQUIPMENT_SLOT_BY_TYPE.get(item.get("type", ""))
    if not slot:
        return [f"{item.get('name', item_id)} is not equippable."]

    previous = state.player.equipment.get(slot)
    state.player.equipment[slot] = item_id
    clamp_player_hp(state.player)
    if previous and previous != item_id:
        return [f"You equip {item['name']} and unequip {_item_name(previous)}."]
    return [f"You equip {item['name']}."]


def equip_best_available(state: GameState) -> List[str]:
    """Equip best-in-slot items available in inventory for each equipment slot."""
    equippable_owned = [
        item_id
        for item_id in state.player.inventory
        if EQUIPMENT_SLOT_BY_TYPE.get(ITEMS.get(item_id, {}).get("type", "")) is not None
    ]
    if not equippable_owned:
        return ["You have no equippable items in your inventory."]

    changes: List[str] = []
    for slot in state.player.equipment:
        current_id = state.player.equipment.get(slot)
        best_id = current_id
        best_score = _item_power_tuple(current_id)

        for item_id in equippable_owned:
            item = ITEMS.get(item_id, {})
            item_slot = EQUIPMENT_SLOT_BY_TYPE.get(item.get("type", ""))
            if item_slot != slot:
                continue
            score = _item_power_tuple(item_id)
            if score > best_score:
                best_id = item_id
                best_score = score

        if best_id and best_id != current_id:
            state.player.equipment[slot] = best_id
            if current_id:
                changes.append(f"{slot}: {_item_name(current_id)} -> {_item_name(best_id)}")
            else:
                changes.append(f"{slot}: none -> {_item_name(best_id)}")

    clamp_player_hp(state.player)
    if not changes:
        return ["Your equipped gear is already best-in-slot for your current inventory."]

    messages = ["Best-in-slot gear equipped:"]
    messages.extend(f"  {line}" for line in changes)
    return messages


def use_item(
    state: GameState,
    item_query: str,
    in_combat: bool = False,
    current_enemy_id: Optional[str] = None,
) -> Tuple[List[str], bool]:
    """Use an item. Returns (messages, consumes_turn)."""
    item_id = find_item_id_by_query(state.player, item_query)
    if not item_id:
        return ([f"You do not have '{item_query}'."], False)

    item = ITEMS.get(item_id, {})
    item_type = item.get("type")
    messages: List[str] = []

    if item_type == "consumable":
        healed = heal_player(state.player, int(item.get("heal_amount", 0)))
        remove_item(state.player, item_id, 1)
        messages.append(f"You use {item['name']} and recover {healed} HP.")
        return messages, True

    if item_id == "mysterious_ring":
        if "ring_surge_active" in state.flags:
            return ["The ring is quiet for now."], False
        state.flags.add("ring_surge_active")
        state.player.temporary_bonuses["attack"] = state.player.temporary_bonuses.get("attack", 0) + 4
        state.player.temporary_bonuses["defense"] = state.player.temporary_bonuses.get("defense", 0) + 2
        messages.append("You rub the ring. Power floods your limbs.")
        return messages, True

    if item_id == "goblin_riddle":
        if in_combat and current_enemy_id == "onyx_witch":
            messages.append("You read the riddle aloud. The witch's binding magic fractures.")
            return messages, True
        messages.append("The riddle speaks in paradox. You sense it is meant for the witch.")
        return messages, False

    if item_id == "crusty_key":
        if (
            state.current_location_id == "witch_terrace"
            and "onyx_witch_defeated" in state.flags
            and "elle_freed" not in state.flags
        ):
            state.flags.add("elle_freed")
            messages.append("The crusty key opens Elle's chains. She is free.")
            return messages, False
        messages.append("The key does not fit anything here.")
        return messages, False

    if item_id == "vial_of_tears":
        if (
            state.current_location_id == "witch_terrace"
            and "elle_freed" in state.flags
            and "elle_cleansed" not in state.flags
        ):
            remove_item(state.player, item_id, 1)
            state.flags.add("elle_cleansed")
            state.victory = True
            messages.append("You pour the vial over Elle's hands. The corruption drains away.")
            messages.append("Elle is restored. The journey is complete.")
            return messages, False
        messages.append("The vial reacts to nothing here.")
        return messages, False

    if item_id == "hoard_treasure":
        if state.current_location_id == "old_shack" and "hoard_delivered" not in state.flags:
            remove_item(state.player, item_id, 1)
            state.player.gold += 180
            state.flags.add("hoard_delivered")
            messages.append("You hand the hoard to the Wise Old Man. He returns most of it for your journey.")
            messages.append("Reward: 180 gold.")
            return messages, False
        messages.append("You decide to hold the hoard for now.")
        return messages, False

    if item_type in {"key", "quest", "aura", "weapon", "armor", "shield", "accessory"}:
        return [f"{item.get('name', item_id)} cannot be directly used right now."], False

    return ["Nothing happens."], False


def clear_ring_surge(state: GameState) -> None:
    """Remove temporary ring bonuses if active."""
    if "ring_surge_active" not in state.flags:
        return
    state.flags.discard("ring_surge_active")
    state.player.temporary_bonuses["attack"] = state.player.temporary_bonuses.get("attack", 0) - 4
    state.player.temporary_bonuses["defense"] = state.player.temporary_bonuses.get("defense", 0) - 2
    if state.player.temporary_bonuses["attack"] == 0:
        state.player.temporary_bonuses.pop("attack", None)
    if state.player.temporary_bonuses["defense"] == 0:
        state.player.temporary_bonuses.pop("defense", None)


def train_skill(state: GameState, skill_name: str, amount: int) -> List[str]:
    """Spend skill points to improve base stats."""
    if amount <= 0:
        return ["Training points must be positive."]
    if state.player.skill_points < amount:
        return ["You do not have enough skill points."]

    skill = skill_name.lower().strip()
    state.player.skill_points -= amount

    if skill in {"attack", "atk"}:
        state.player.base_attack += amount
        return [f"Attack trained by +{amount}."]
    if skill in {"defense", "def", "guard"}:
        state.player.base_defense += amount
        return [f"Defense trained by +{amount}."]
    if skill in {"health", "hp", "vitality"}:
        state.player.base_max_hp += amount * 3
        state.player.hp += amount * 3
        clamp_player_hp(state.player)
        return [f"Health trained by +{amount * 3} max HP."]

    state.player.skill_points += amount
    return ["Unknown skill. Use attack, defense, or health."]


def train_all_equally(state: GameState) -> List[str]:
    """Spend skill points equally across attack, defense, and health."""
    available = state.player.skill_points
    if available < 3:
        return ["You need at least 3 skill points to train all stats equally."]

    per_stat = available // 3
    spent = per_stat * 3
    remaining = available - spent

    state.player.skill_points = remaining
    state.player.base_attack += per_stat
    state.player.base_defense += per_stat
    hp_gain = per_stat * 3
    state.player.base_max_hp += hp_gain
    state.player.hp += hp_gain
    clamp_player_hp(state.player)

    messages = [
        f"Trained equally: attack +{per_stat}, defense +{per_stat}, health +{hp_gain} max HP.",
    ]
    if remaining > 0:
        messages.append(f"{remaining} skill point(s) remain unspent.")
    return messages


def train_allocation(state: GameState, attack_pts: int, defense_pts: int, health_pts: int) -> List[str]:
    """Spend an explicit training split across attack/defense/health."""
    if attack_pts < 0 or defense_pts < 0 or health_pts < 0:
        return ["Training values cannot be negative."]

    total = attack_pts + defense_pts + health_pts
    if total <= 0:
        return ["Provide at least one positive training value."]
    if state.player.skill_points < total:
        return [f"You do not have enough skill points (need {total}, have {state.player.skill_points})."]

    state.player.skill_points -= total
    state.player.base_attack += attack_pts
    state.player.base_defense += defense_pts
    hp_gain = health_pts * 3
    state.player.base_max_hp += hp_gain
    state.player.hp += hp_gain
    clamp_player_hp(state.player)

    return [
        f"Training applied: attack +{attack_pts}, defense +{defense_pts}, health +{hp_gain} max HP.",
        f"Skill points remaining: {state.player.skill_points}.",
    ]


def ensure_core_skills(state: GameState) -> None:
    """Grant baseline combat skills when taught by the old man."""
    state.player.skills.update({"focus strike", "guard stance", "second wind"})


def has_riddle(state: GameState) -> bool:
    return has_item(state.player, "goblin_riddle")
