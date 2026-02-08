"""Turn-based combat system."""

from __future__ import annotations

from typing import List, Optional

from content.enemies import ENEMIES
from content.items import ITEMS
from game import ui
from game.state import Encounter, GameState, clamp_player_hp, get_effective_stats, has_item
from systems.loot import clear_ring_surge, grant_rewards, use_item


BOSS_FLAGS = {
    "giant_frog": "frog_defeated",
    "dragon": "dragon_defeated",
    "ogre": "ogre_defeated",
    "goblin_army": "goblin_army_defeated",
    "king_makor": "makor_defeated",
    "onyx_witch": "onyx_witch_defeated",
}


BOSS_TITLES = {
    "giant_frog": "Swampbreaker",
    "dragon": "Peakslayer",
    "ogre": "Hoardbreaker",
    "goblin_army": "Road Reaper",
    "king_makor": "Rotbane",
    "onyx_witch": "Witchfall Champion",
}


def _enemy(enemy_id: str) -> dict:
    return ENEMIES[enemy_id]


def _format_intent(encounter: Encounter, enemy: dict) -> str:
    intents = enemy.get("intents", [])
    if not intents:
        return f"{enemy['name']} sizes you up."
    intent = intents[encounter.intent_index % len(intents)]
    return intent.get("telegraph", f"{enemy['name']} prepares an attack.")


def _intent_payload(encounter: Encounter, enemy: dict) -> dict:
    intents = enemy.get("intents", [])
    if not intents:
        return {"name": "Strike", "base_damage": int(enemy.get("attack", 1)), "defend_multiplier": 0.5}
    return intents[encounter.intent_index % len(intents)]


def _health_snapshot_lines(state: GameState, enemy: dict, enemy_hp: Optional[int] = None) -> List[str]:
    if enemy_hp is None:
        if state.active_encounter:
            enemy_hp = state.active_encounter.current_hp
        else:
            enemy_hp = 0
    enemy_hp = max(0, int(enemy_hp))
    enemy_max_hp = int(enemy.get("hp", max(1, enemy_hp)))
    player_max_hp = int(get_effective_stats(state.player)["max_hp"])
    return ui.combat_health_lines(
        player_hp=state.player.hp,
        player_max_hp=player_max_hp,
        enemy_name=enemy.get("name", "Enemy"),
        enemy_hp=enemy_hp,
        enemy_max_hp=enemy_max_hp,
    )


def _tick_cooldowns(state: GameState) -> None:
    updated = {}
    for skill, turns in state.player.cooldowns.items():
        if turns > 1:
            updated[skill] = turns - 1
    state.player.cooldowns = updated


def start_encounter(state: GameState, enemy_id: str) -> List[str]:
    """Create an encounter if not already in one."""
    if state.active_encounter:
        return []

    enemy = _enemy(enemy_id)
    encounter = Encounter(enemy_id=enemy_id, current_hp=int(enemy["hp"]))
    if enemy.get("special") == "goblin_negotiation":
        encounter.special_phase = "negotiation"
    if enemy.get("special") == "witch_barrier":
        encounter.witch_barrier_active = True
    state.active_encounter = encounter

    messages: List[str] = []
    messages.extend(enemy.get("pre_dialogue", []))

    if enemy_id == "king_makor" and has_item(state.player, "mysterious_ring"):
        if "ring_surge_active" not in state.flags:
            state.flags.add("ring_surge_active")
            state.player.temporary_bonuses["attack"] = state.player.temporary_bonuses.get("attack", 0) + 4
            state.player.temporary_bonuses["defense"] = state.player.temporary_bonuses.get("defense", 0) + 2
            messages.append("The mysterious ring flares and empowers you.")

    messages.append(f"Encounter started: {enemy['name']} ({encounter.current_hp} HP).")
    if encounter.special_phase != "negotiation":
        messages.append(_format_intent(encounter, enemy))
    return messages


def encounter_status(state: GameState) -> List[str]:
    """Return current encounter status lines."""
    if not state.active_encounter:
        return []
    enemy = _enemy(state.active_encounter.enemy_id)
    lines = [f"Enemy: {enemy['name']} HP {state.active_encounter.current_hp}/{enemy['hp']}"]
    if state.active_encounter.special_phase == "negotiation":
        lines.append("Actions: joke, bribe, or fight.")
    else:
        lines.append(_format_intent(state.active_encounter, enemy))
    return lines


def _player_attack_damage(state: GameState, enemy: dict, multiplier: float = 1.0) -> int:
    player_stats = get_effective_stats(state.player)
    attack_value = int(player_stats["attack"] * multiplier)
    damage = attack_value + state.rng.randint(-2, 3) - int(enemy.get("defense", 0) / 2)
    return max(1, damage)


def _enemy_attack_damage(state: GameState, enemy: dict, encounter: Encounter, payload: dict) -> int:
    player_stats = get_effective_stats(state.player)
    base = int(payload.get("base_damage", enemy.get("attack", 1)))
    damage = base + state.rng.randint(-3, 3) - int(player_stats["defense"] / 3)
    damage = max(1, damage)
    if encounter.player_defending:
        multiplier = float(payload.get("defend_multiplier", 0.5))
        damage = max(1, int(damage * multiplier))
    return damage


def _award_title(state: GameState, enemy_id: str) -> Optional[str]:
    title = BOSS_TITLES.get(enemy_id)
    if not title:
        return None
    if title not in state.player.titles:
        state.player.titles.append(title)
        return title
    return None


def _resolve_victory(state: GameState) -> List[str]:
    encounter = state.active_encounter
    if not encounter:
        return []
    enemy_id = encounter.enemy_id
    enemy = _enemy(enemy_id)
    messages: List[str] = [f"You defeat {enemy['name']}."]
    messages.extend(enemy.get("post_dialogue", []))

    boss_flag = BOSS_FLAGS.get(enemy_id)
    if boss_flag:
        state.flags.add(boss_flag)
    if enemy_id == "goblin_army":
        state.flags.add("goblin_pass_granted")
    if enemy_id == "onyx_witch" and has_item(state.player, "crusty_key"):
        state.flags.add("elle_freed")
        messages.append("You unlock Elle's chains with the crusty key.")

    title = _award_title(state, enemy_id)
    if title:
        messages.append(f"Title earned: {title}.")

    messages.extend(grant_rewards(state, enemy_id))

    state.active_encounter = None
    clear_ring_surge(state)
    return messages


def _penalty_on_goblin_loss(state: GameState) -> Optional[str]:
    if state.rng.random() > 0.5:
        return None
    choice = state.rng.choice(["attack", "defense", "health"])
    if choice == "attack":
        state.player.base_attack = max(1, state.player.base_attack - 1)
        return "The goblins beat you down. Base attack is reduced by 1."
    if choice == "defense":
        state.player.base_defense = max(0, state.player.base_defense - 1)
        return "The goblins bruise your guard. Base defense is reduced by 1."
    state.player.base_max_hp = max(10, state.player.base_max_hp - 1)
    state.player.hp = max(1, state.player.hp - 1)
    clamp_player_hp(state.player)
    return "The goblins leave deep wounds. Base health is reduced by 1."


def _resolve_defeat(state: GameState, enemy_id: str) -> List[str]:
    messages = ["You collapse and lose consciousness."]
    if enemy_id == "goblin_army":
        penalty = _penalty_on_goblin_loss(state)
        if penalty:
            messages.append(penalty)
    state.active_encounter = None
    state.current_location_id = "old_shack"
    state.player.hp = max(1, int(get_effective_stats(state.player)["max_hp"] * 0.5))
    clear_ring_surge(state)
    messages.append("You wake in the Old Shack, battered but alive.")
    return messages


def _enemy_turn(state: GameState) -> List[str]:
    encounter = state.active_encounter
    if not encounter:
        return []
    enemy = _enemy(encounter.enemy_id)
    payload = _intent_payload(encounter, enemy)
    damage = _enemy_attack_damage(state, enemy, encounter, payload)
    state.player.hp -= damage
    clamp_player_hp(state.player)

    messages = [f"{enemy['name']} uses {payload.get('name', 'attack')} and deals {damage} damage."]

    if encounter.enemy_id == "onyx_witch" and encounter.witch_barrier_active:
        curse = 4
        state.player.hp = max(0, state.player.hp - curse)
        messages.append(f"The binding curse drains {curse} more HP.")

    messages.extend(_health_snapshot_lines(state, enemy))

    if state.player.hp <= 0:
        return messages + _resolve_defeat(state, encounter.enemy_id)

    encounter.player_defending = False
    encounter.intent_index += 1
    encounter.turn_count += 1
    _tick_cooldowns(state)

    if state.active_encounter:
        messages.append(_format_intent(encounter, enemy))
    return messages


def _handle_goblin_negotiation(state: GameState, action: str) -> List[str]:
    encounter = state.active_encounter
    if not encounter:
        return []
    if action == "joke":
        state.active_encounter = None
        state.flags.add("goblin_pass_granted")
        return [
            "You tell a terrible joke about goblin fashion.",
            "The mob erupts in laughter and cuts your ropes.",
            "They let you pass, still giggling.",
        ]
    if action == "bribe":
        if state.player.gold <= 0:
            encounter.special_phase = "combat"
            return ["You have no gold. The goblins snarl and charge. Fight begins."]
        taken = state.player.gold
        state.player.gold = 0
        state.active_encounter = None
        state.flags.add("goblin_pass_granted")
        return [
            f"You offer your coin. They take all {taken} gold and shove you onward.",
            "You survive the ambush, but gain no riddle.",
        ]
    if action == "fight":
        encounter.special_phase = "combat"
        return [
            "You pull free and draw steel. The goblins howl with laughter.",
            _format_intent(encounter, _enemy(encounter.enemy_id)),
        ]
    return ["The goblins mock you. Choose `joke`, `bribe`, or `fight`."]


def attempt_run(state: GameState) -> List[str]:
    """Attempt to flee the current encounter."""
    encounter = state.active_encounter
    if not encounter:
        return ["There is nothing to run from."]

    enemy = _enemy(encounter.enemy_id)
    if encounter.special_phase == "negotiation":
        return ["You are tied up. Running is not an option. Choose joke, bribe, or fight."]

    run_chance = 0.65 if enemy.get("category") == "normal" else 0.28
    if encounter.enemy_id == "goblin_army":
        run_chance = 0.22

    if state.rng.random() < run_chance:
        state.active_encounter = None
        clear_ring_surge(state)
        return [f"You escape from {enemy['name']}."]

    messages = [f"You fail to escape {enemy['name']}."]
    messages.extend(_enemy_turn(state))
    return messages


def player_action(state: GameState, action: str, args: Optional[list[str]] = None) -> List[str]:
    """Resolve one player action in combat."""
    encounter = state.active_encounter
    if not encounter:
        return ["There is nothing to fight."]

    args = args or []
    enemy = _enemy(encounter.enemy_id)
    messages: List[str] = []

    if encounter.special_phase == "negotiation":
        return _handle_goblin_negotiation(state, action)

    consume_turn = True

    if action == "fight":
        if encounter.witch_barrier_active and encounter.enemy_id == "onyx_witch":
            messages.append("Your strike stops against black magic. You cannot attack yet.")
        else:
            damage = _player_attack_damage(state, enemy)
            encounter.current_hp -= damage
            messages.append(f"You strike {enemy['name']} for {damage} damage.")
            messages.extend(_health_snapshot_lines(state, enemy))

    elif action == "defend":
        encounter.player_defending = True
        messages.append("You brace for impact.")

    elif action == "skill":
        skill_name = " ".join(args).strip().lower()
        if not skill_name:
            return ["Specify a skill. Try: skill focus strike"]
        if skill_name not in state.player.skills:
            return [f"You have not learned '{skill_name}'."]
        if state.player.cooldowns.get(skill_name, 0) > 0:
            return [f"{skill_name} is on cooldown for {state.player.cooldowns[skill_name]} more turn(s)."]

        if skill_name == "focus strike":
            if encounter.witch_barrier_active and encounter.enemy_id == "onyx_witch":
                messages.append("Focus Strike breaks against the witch's binding spell.")
            else:
                damage = _player_attack_damage(state, enemy, multiplier=1.8)
                encounter.current_hp -= damage
                messages.append(f"Focus Strike lands for {damage} damage.")
                messages.extend(_health_snapshot_lines(state, enemy))
            state.player.cooldowns[skill_name] = 2
        elif skill_name == "guard stance":
            encounter.player_defending = True
            state.player.hp = min(get_effective_stats(state.player)["max_hp"], state.player.hp + 6)
            messages.append("You enter Guard Stance, reducing incoming damage and restoring 6 HP.")
            state.player.cooldowns[skill_name] = 3
        elif skill_name == "second wind":
            state.player.hp = min(get_effective_stats(state.player)["max_hp"], state.player.hp + 16)
            messages.append("Second Wind restores 16 HP.")
            state.player.cooldowns[skill_name] = 4
        else:
            messages.append("That skill has no effect.")
            consume_turn = False

    elif action in {"use", "read"}:
        if not args:
            return ["Use what? Example: use minor potion"]
        item_query = " ".join(args)
        item_messages, consume_turn = use_item(
            state,
            item_query,
            in_combat=True,
            current_enemy_id=encounter.enemy_id,
        )
        messages.extend(item_messages)

        if encounter.enemy_id == "onyx_witch" and encounter.witch_barrier_active:
            item_id = None
            for owned_item_id in state.player.inventory:
                owned_name = ITEMS.get(owned_item_id, {}).get("name", "").lower()
                if item_query.lower() in {owned_item_id, owned_name} or item_query.lower() in owned_name:
                    item_id = owned_item_id
                    break
            if item_query.lower() == "goblin riddle":
                item_id = "goblin_riddle"
            if item_id == "goblin_riddle":
                encounter.witch_barrier_active = False
                messages.append("The riddle's final line shatters the witch's black binding.")

    elif action in {"joke", "bribe"}:
        messages.append("That only works when negotiating with the goblin army.")
        consume_turn = False

    else:
        return ["Unknown combat action."]

    if encounter.current_hp <= 0:
        return messages + _resolve_victory(state)

    if consume_turn and state.active_encounter:
        messages.extend(_enemy_turn(state))

    return messages
