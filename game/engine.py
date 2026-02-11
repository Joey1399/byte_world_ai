"""Main game loop and command dispatch."""

from __future__ import annotations

from collections import deque
import os
import sys
from typing import Callable, List

from content.enemies import ENEMIES
from content.items import EQUIPMENT_SLOT_BY_TYPE, ITEMS
from content.world import LOCATIONS, NPCS
from game.commands import parse_command
from game.state import GameState, get_effective_stats
from game import ui
from systems import combat, exploration, loot, quest


class Engine:
    """CLI engine for byte_world_ai."""

    def __init__(self, input_fn: Callable[[str], str] = input, output_fn: Callable[[str], None] = print):
        self.input_fn = input_fn
        self.output_fn = output_fn

    def _emit_lines(self, messages: List[str]) -> None:
        text = ui.format_messages(messages)
        if text:
            self.output_fn(text)

    def _emit_action(self, messages: List[str]) -> None:
        text = ui.format_action_block(messages)
        if text:
            self.output_fn(text)

    def _clear_terminal(self) -> None:
        """Clear the terminal screen in interactive sessions."""
        no_clear = os.getenv("BYTE_WORLD_AI_NO_CLEAR") == "1" or os.getenv("BYTE_WORLD_NO_CLEAR") == "1"
        if no_clear:
            return
        force_clear = os.getenv("BYTE_WORLD_AI_FORCE_CLEAR") == "1" or os.getenv("BYTE_WORLD_FORCE_CLEAR") == "1"
        if not (sys.stdout.isatty() or force_clear):
            return
        self.output_fn("\033[2J\033[H")

    def _add_action(self, actions: dict[str, str], command: str, description: str) -> None:
        if command and command not in actions:
            actions[command] = description

    def _exit_requirement_met(self, state: GameState, requirement: dict) -> bool:
        all_flags = requirement.get("all_flags", [])
        any_flags = requirement.get("any_flags", [])
        if all_flags and any(flag not in state.flags for flag in all_flags):
            return False
        if any_flags and all(flag not in state.flags for flag in any_flags):
            return False
        return True

    def _visible_npc_names(self, state: GameState, location: dict) -> List[str]:
        names: List[str] = []
        for npc_id in location.get("npcs", []):
            if npc_id == "elle" and "onyx_witch_defeated" not in state.flags:
                continue
            names.append(NPCS.get(npc_id, {}).get("name", npc_id))
        return names

    def _item_query(self, item_id: str) -> str:
        return ITEMS.get(item_id, {}).get("name", item_id).lower()

    def _item_stat_summary(self, item: dict) -> str:
        pieces: List[str] = []
        attack = int(item.get("attack_bonus", 0))
        defense = int(item.get("defense_bonus", 0))
        max_hp = int(item.get("max_hp_bonus", 0))
        if attack:
            pieces.append(f"{attack:+d} ATK")
        if defense:
            pieces.append(f"{defense:+d} DEF")
        if max_hp:
            pieces.append(f"{max_hp:+d} max HP")
        if not pieces:
            return ""
        return " (" + ", ".join(pieces) + ")"

    def _talk_description(self, state: GameState, npc_name: str) -> str:
        key = npc_name.lower()
        if key == "wise old man":
            if "met_old_man" not in state.flags:
                return "Starts his intro dialogue and teaches core combat skills."
            if "hoard_treasure" in state.player.inventory and "hoard_delivered" not in state.flags:
                return "Gives guidance and can accept the hoard via `use hoard`."
            return "Get guidance and story hints."
        if key == "elle":
            if "elle_freed" not in state.flags:
                return "She is chained right now."
            if "elle_met" not in state.flags:
                return "Starts Elle's post-rescue dialogue."
            if "elle_cleansed" not in state.flags:
                return "Gives hints about cleansing the corruption."
            return "Closing dialogue after ending."
        return "Talk to this NPC."

    def _use_item_description(self, state: GameState, item_id: str, in_combat: bool = False) -> str:
        item = ITEMS.get(item_id, {})
        item_type = item.get("type", "")
        max_hp = get_effective_stats(state.player)["max_hp"]
        encounter = state.active_encounter

        if item_type == "consumable":
            heal = int(item.get("heal_amount", 0))
            missing = max(0, max_hp - state.player.hp)
            if missing > 0:
                return f"Heals up to {heal} HP (currently missing {missing})."
            return f"Heals up to {heal} HP (you are already at full HP)."

        if item_id == "mysterious_ring":
            if "ring_surge_active" in state.flags:
                return "Ring surge is already active; using now has no effect."
            return "Triggers a temporary +4 ATK / +2 DEF surge."

        if item_id == "goblin_riddle":
            if (
                in_combat
                and encounter
                and encounter.enemy_id == "onyx_witch"
                and encounter.witch_barrier_active
            ):
                return "Breaks the Onyx Witch barrier so your attacks can land."
            return "Read for lore now; its key combat effect is for the Onyx Witch."

        if item_id == "crusty_key":
            if (
                state.current_location_id == "witch_terrace"
                and "onyx_witch_defeated" in state.flags
                and "elle_freed" not in state.flags
            ):
                return "Unlocks Elle's chains."
            return "No matching lock in your current state."

        if item_id == "vial_of_tears":
            if (
                state.current_location_id == "witch_terrace"
                and "elle_freed" in state.flags
                and "elle_cleansed" not in state.flags
            ):
                return "Cleanses Elle and completes the main storyline."
            return "No reaction in this state."

        if item_id == "hoard_treasure":
            if state.current_location_id == "old_shack" and "hoard_delivered" not in state.flags:
                return "Turns in the hoard to the Wise Old Man for 180 gold."
            return "No turn-in available here."

        if item_type in EQUIPMENT_SLOT_BY_TYPE:
            slot = EQUIPMENT_SLOT_BY_TYPE[item_type]
            return f"No direct use. Equip it in the {slot} slot."

        if item_type in {"key", "quest", "boon", "aura"}:
            return "No immediate effect in the current state."

        return "Try using it."

    def _skill_description(self, skill_name: str) -> str:
        if skill_name == "focus strike":
            return "Heavy attack (about 1.8x damage), 2-turn cooldown."
        if skill_name == "guard stance":
            return "Defend this turn and restore 6 HP, 3-turn cooldown."
        if skill_name == "second wind":
            return "Restore 16 HP, 4-turn cooldown."
        return "Use a learned combat skill."

    def _action_lines(self, actions: dict[str, str], heading: str) -> List[str]:
        lines = [f"{heading} ({len(actions)}):"]
        for command, description in actions.items():
            lines.append(f"  {command}: {description}")
        return lines

    def _combat_item_relevant(self, item_id: str, encounter_enemy_id: str) -> bool:
        item_type = ITEMS.get(item_id, {}).get("type")
        if item_type == "consumable":
            return True
        if item_id == "mysterious_ring":
            return True
        if item_id == "goblin_riddle" and encounter_enemy_id == "onyx_witch":
            return True
        return False

    def _neighbors(self, state: GameState, location_id: str, respect_locks: bool) -> List[tuple[str, str]]:
        location = LOCATIONS[location_id]
        exits = location.get("exits", {})
        requirements = location.get("exit_requirements", {})
        neighbors: List[tuple[str, str]] = []
        for direction, next_location_id in exits.items():
            req = requirements.get(direction)
            if respect_locks and req and not self._exit_requirement_met(state, req):
                continue
            neighbors.append((direction, next_location_id))
        return neighbors

    def _shortest_direction_path(
        self,
        state: GameState,
        start_location_id: str,
        target_location_id: str,
        respect_locks: bool,
    ) -> List[str] | None:
        if start_location_id == target_location_id:
            return []

        frontier: deque[tuple[str, List[str]]] = deque([(start_location_id, [])])
        visited = {start_location_id}

        while frontier:
            location_id, path = frontier.popleft()
            for direction, next_location_id in self._neighbors(state, location_id, respect_locks):
                if next_location_id in visited:
                    continue
                next_path = [*path, direction]
                if next_location_id == target_location_id:
                    return next_path
                visited.add(next_location_id)
                frontier.append((next_location_id, next_path))
        return None

    def _recommended_map_step(self, state: GameState) -> tuple[str | None, str | None]:
        target_by_stage = {
            "awakening": "old_shack",
            "swamp_secret": "swamp",
            "mountain_flame": "mountain_peak",
            "castle_road": "desolate_road",
            "black_hall": "black_hall",
            "witch_bane": "witch_terrace",
            "rescue_elle": "witch_terrace",
            "homecoming": "old_shack",
        }
        target_id = target_by_stage.get(state.quest_stage)
        if not target_id:
            return None, None
        if target_id == state.current_location_id:
            return target_id, None

        open_path = self._shortest_direction_path(
            state,
            start_location_id=state.current_location_id,
            target_location_id=target_id,
            respect_locks=True,
        )
        if open_path:
            return target_id, open_path[0]

        eventual_path = self._shortest_direction_path(
            state,
            start_location_id=state.current_location_id,
            target_location_id=target_id,
            respect_locks=False,
        )
        if eventual_path:
            return target_id, eventual_path[0]

        return target_id, None

    def _map_direction_labels(self, state: GameState, recommended_direction: str | None) -> dict[str, str]:
        current = LOCATIONS[state.current_location_id]
        exits = current.get("exits", {})
        requirements = current.get("exit_requirements", {})

        labels: dict[str, str] = {}
        for direction in ("north", "east", "south", "west", "up", "down"):
            destination_id = exits.get(direction)
            if not destination_id:
                labels[direction] = "---"
                continue

            destination_name = LOCATIONS.get(destination_id, {}).get("name", destination_id)
            req = requirements.get(direction)
            if req and not self._exit_requirement_met(state, req):
                labels[direction] = f"{destination_name} (locked)"
            else:
                labels[direction] = destination_name
            if direction == recommended_direction:
                labels[direction] = f"{labels[direction]} (recommended)"
        return labels

    def _map_route_lines(self, state: GameState, recommended_target_id: str | None) -> List[str]:
        current_id = state.current_location_id
        lines: List[str] = []

        key_targets = [
            ("old_shack", "Old Shack"),
            ("swamp", "Swamp"),
            ("mountain_peak", "Dragon Mountain Peak"),
            ("desolate_road", "Desolate Road"),
            ("black_hall", "Black Hall"),
            ("witch_terrace", "Witch's Terrace"),
        ]

        for target_id, label in key_targets:
            suffix = " (recommended)" if target_id == recommended_target_id else ""
            if target_id == current_id:
                lines.append(f"{label}: you are here.{suffix}")
                continue

            open_path = self._shortest_direction_path(
                state,
                start_location_id=current_id,
                target_location_id=target_id,
                respect_locks=True,
            )
            if open_path is not None:
                first_step = open_path[0]
                lines.append(f"{label}: go {first_step}.{suffix}")
                continue

            eventual_path = self._shortest_direction_path(
                state,
                start_location_id=current_id,
                target_location_id=target_id,
                respect_locks=False,
            )
            if eventual_path is not None:
                lines.append(f"{label}: locked now (later go {eventual_path[0]}).{suffix}")
            else:
                lines.append(f"{label}: no route found.{suffix}")

        return lines

    def _exploration_actions(self, state: GameState) -> dict[str, str]:
        location = LOCATIONS[state.current_location_id]
        actions: dict[str, str] = {}
        has_equippable_inventory = False
        encounter_names = [
            ENEMIES.get(enemy_id, {}).get("name", enemy_id)
            for enemy_id, _ in location.get("encounters", [])
        ]
        encounter_note = ""
        if encounter_names and float(location.get("encounter_chance", 0.0)) > 0:
            if len(encounter_names) <= 3:
                preview = ", ".join(encounter_names)
                encounter_note = f" Travel can trigger combat with {preview}."
            else:
                preview = ", ".join(encounter_names[:3])
                encounter_note = (
                    f" Travel can trigger combat with {len(encounter_names)} creature types "
                    f"(e.g. {preview})."
                )

        self._add_action(actions, "look", "Re-describe your current location and exits.")
        self._add_action(actions, "sense", "Get environmental hints for this area.")
        self._add_action(actions, "status", "View HP, combat stats, level, and equipped gear.")
        self._add_action(actions, "quest", "Show your current objective and hint.")
        if location.get("encounters", []):
            self._add_action(
                actions,
                "hunt",
                "Force a creature encounter in this area for farming.",
            )
        self._add_action(actions, "inventory", "List your inventory items.")
        self._add_action(actions, "help", "Open the full command menu.")
        self._add_action(actions, "quit", "End the game session.")

        exits = location.get("exits", {})
        exit_requirements = location.get("exit_requirements", {})
        for direction in sorted(exits.keys()):
            requirement = exit_requirements.get(direction)
            if requirement and not self._exit_requirement_met(state, requirement):
                continue
            destination_id = exits[direction]
            destination_name = LOCATIONS.get(destination_id, {}).get("name", destination_id)
            self._add_action(
                actions,
                f"move {direction}",
                f"Travel to {destination_name}.{encounter_note}".strip(),
            )

        for npc_name in self._visible_npc_names(state, location):
            self._add_action(
                actions,
                f"talk {npc_name.lower()}",
                self._talk_description(state, npc_name),
            )

        for item_id in sorted(state.player.inventory):
            item = ITEMS.get(item_id, {})
            item_type = item.get("type", "")
            query = self._item_query(item_id)

            if item_type in EQUIPMENT_SLOT_BY_TYPE:
                has_equippable_inventory = True
                slot = EQUIPMENT_SLOT_BY_TYPE[item_type]
                current = state.player.equipment.get(slot)
                stat_text = self._item_stat_summary(item)
                if current == item_id:
                    equip_desc = f"Already equipped in {slot} slot{stat_text}."
                elif current:
                    current_name = ITEMS.get(current, {}).get("name", current)
                    equip_desc = f"Equip in {slot} slot (replaces {current_name}){stat_text}."
                else:
                    equip_desc = f"Equip in {slot} slot{stat_text}."
                self._add_action(actions, f"equip {query}", equip_desc)

            use_desc = self._use_item_description(state, item_id, in_combat=False)
            self._add_action(actions, f"use {query}", use_desc)

            if item_id == "goblin_riddle":
                self._add_action(
                    actions,
                    f"read {query}",
                    "Read the riddle text; key to the Onyx Witch fight.",
                )

        if has_equippable_inventory:
            self._add_action(
                actions,
                "equip all",
                "Auto-equip the best available item for every gear slot.",
            )

        if state.player.skill_points > 0:
            self._add_action(
                actions,
                "train attack 1",
                f"Spend 1 skill point for +1 base ATK ({state.player.skill_points} available).",
            )
            self._add_action(
                actions,
                "train defense 1",
                f"Spend 1 skill point for +1 base DEF ({state.player.skill_points} available).",
            )
            self._add_action(
                actions,
                "train health 1",
                f"Spend 1 skill point for +3 max HP ({state.player.skill_points} available).",
            )
            if state.player.skill_points >= 3:
                self._add_action(
                    actions,
                    "train all",
                    "Split skill points equally across attack, defense, and health.",
                )
            self._add_action(
                actions,
                "train a,b,c",
                "Train exact points as attack,defense,health (example: train 3,4,3).",
            )

        return actions

    def _encounter_actions(self, state: GameState) -> dict[str, str]:
        encounter = state.active_encounter
        if not encounter:
            return {}

        enemy = ENEMIES.get(encounter.enemy_id, {})
        enemy_name = enemy.get("name", encounter.enemy_id)
        actions: dict[str, str] = {}

        if encounter.special_phase == "negotiation":
            self._add_action(actions, "joke", f"Try to make {enemy_name} laugh and avoid combat.")
            self._add_action(
                actions,
                "bribe",
                f"Pay all your gold ({state.player.gold}) to avoid combat.",
            )
            self._add_action(actions, "fight", f"Start full combat against {enemy_name}.")
        else:
            self._add_action(actions, "fight", f"Attack {enemy_name} with a basic strike.")
            self._add_action(actions, "defend", "Reduce damage from the next enemy hit.")
            run_chance = 0.65 if enemy.get("category") == "normal" else 0.28
            if encounter.enemy_id == "goblin_army":
                run_chance = 0.22
            self._add_action(
                actions,
                "run",
                f"Attempt to escape (about {int(run_chance * 100)}% success chance).",
            )

            for skill_name in sorted(state.player.skills):
                cooldown = state.player.cooldowns.get(skill_name, 0)
                skill_desc = self._skill_description(skill_name)
                if cooldown > 0:
                    skill_desc = f"{skill_desc} Currently on cooldown ({cooldown} turn(s))."
                self._add_action(actions, f"skill {skill_name}", skill_desc)

            for item_id in sorted(state.player.inventory):
                if not self._combat_item_relevant(item_id, encounter.enemy_id):
                    continue
                query = self._item_query(item_id)
                self._add_action(
                    actions,
                    f"use {query}",
                    self._use_item_description(state, item_id, in_combat=True),
                )
                if item_id == "goblin_riddle":
                    if encounter.enemy_id == "onyx_witch" and encounter.witch_barrier_active:
                        read_desc = "Read now to break the witch's barrier."
                    else:
                        read_desc = "Read the riddle text; mainly useful against the witch."
                    self._add_action(actions, f"read {query}", read_desc)

        return actions

    def _build_input_hints(self, state: GameState) -> List[str]:
        if state.active_encounter:
            return self._action_lines(self._encounter_actions(state), "Combat actions")
        return self._action_lines(self._exploration_actions(state), "Available actions")

    def _build_status_payload(self, state: GameState) -> dict:
        stats = get_effective_stats(state.player)
        equipment = {
            slot: (ITEMS.get(item_id, {}).get("name", item_id) if item_id else "none")
            for slot, item_id in state.player.equipment.items()
        }
        return {
            "name": state.player.name,
            "level": state.player.level,
            "hp": state.player.hp,
            "max_hp": stats["max_hp"],
            "attack": stats["attack"],
            "defense": stats["defense"],
            "xp": state.player.xp,
            "skill_points": state.player.skill_points,
            "gold": state.player.gold,
            "titles": list(state.player.titles),
            "equipment": equipment,
        }

    def _resolve_turn(self, state: GameState, command: str, args: List[str]) -> List[str]:
        """Resolve one parsed command including quest/victory side effects."""
        action_messages = self._handle_command(state, command, args)

        quest_messages = quest.check_and_advance(state)
        action_messages.extend(quest_messages)

        if state.victory and "victory_announced" not in state.flags:
            state.flags.add("victory_announced")
            action_messages.extend(
                [
                    "You have completed the main storyline.",
                    "You can keep exploring or type `quit`.",
                ]
            )

        return action_messages

    def _render_screen(
        self,
        state: GameState,
        action_messages: List[str] | None = None,
        include_banner: bool = False,
    ) -> str:
        """Render the current game screen for terminal-like clients."""
        parts: List[str] = []
        if include_banner:
            parts.append(ui.banner())

        if action_messages:
            action_block = ui.format_action_block(action_messages)
            if action_block:
                parts.append(action_block)

        if not state.game_over:
            hints = ui.format_messages(self._build_input_hints(state))
            if hints:
                parts.append(hints)

        return "\n".join(part for part in parts if part)

    def initial_screen(self, state: GameState) -> str:
        """Render first screen content for a new game session."""
        intro_messages = [*exploration.look(state), "Type `help` for commands."]
        return self._render_screen(state, action_messages=intro_messages, include_banner=True)

    def process_raw_command(self, state: GameState, raw_command: str) -> str:
        """Parse and resolve one raw command and return rendered screen text."""
        command, args = parse_command(raw_command)
        if not command:
            return self._render_screen(state)
        action_messages = self._resolve_turn(state, command, args)
        return self._render_screen(state, action_messages=action_messages)

    def _handle_command(self, state: GameState, command: str, args: List[str]) -> List[str]:
        if state.active_encounter:
            allowed = {
                "help",
                "status",
                "inventory",
                "use",
                "read",
                "fight",
                "defend",
                "skill",
                "run",
                "quest",
                "joke",
                "bribe",
                "quit",
            }
            if command not in allowed:
                return ["You are in an encounter. Use combat commands or `run`."]

        if command == "help":
            return [ui.help_text()]

        if command == "status":
            messages = [ui.format_status(self._build_status_payload(state))]
            if state.active_encounter:
                messages.extend(combat.encounter_status(state))
            return messages

        if command == "look":
            messages = exploration.look(state)
            if state.active_encounter:
                messages.extend(combat.encounter_status(state))
            return messages

        if command == "sense":
            return exploration.sense(state)

        if command == "hunt":
            return exploration.hunt(state)

        if command == "move":
            if not args:
                return ["Move where? Example: move north"]
            return exploration.move(state, args[0])

        if command == "inventory":
            return [ui.format_inventory(state.player.inventory)]

        if command == "equip":
            if not args:
                return ["Equip what? Example: equip crusty sword, or use `equip all`."]
            if len(args) == 1 and args[0].lower() == "all":
                return loot.equip_best_available(state)
            return loot.equip_item(state, " ".join(args))

        if command in {"use", "read"}:
            if not args:
                return ["Use what? Example: use minor potion"]
            if state.active_encounter:
                return combat.player_action(state, command, args)
            messages, _ = loot.use_item(state, " ".join(args))
            return messages

        if command == "fight":
            return combat.player_action(state, "fight", args)

        if command == "defend":
            return combat.player_action(state, "defend", args)

        if command == "skill":
            return combat.player_action(state, "skill", args)

        if command == "run":
            return combat.attempt_run(state)

        if command == "joke":
            return combat.player_action(state, "joke", args)

        if command == "bribe":
            return combat.player_action(state, "bribe", args)

        if command == "train":
            if not args:
                return ["Train what? Examples: train attack 2, train all, train 3,4,3"]

            raw_train = " ".join(args).strip()
            lowered = raw_train.lower()

            if lowered == "all":
                return loot.train_all_equally(state)

            if "," in raw_train:
                parts = [part.strip() for part in raw_train.split(",")]
                if len(parts) != 3 or any(not part for part in parts):
                    return ["Use format: train attack,defense,health (example: train 3,4,3)."]
                try:
                    attack_pts, defense_pts, health_pts = (int(parts[0]), int(parts[1]), int(parts[2]))
                except ValueError:
                    return ["Training allocation must be numbers. Example: train 3,4,3"]
                return loot.train_allocation(state, attack_pts, defense_pts, health_pts)

            skill_name = args[0]
            amount = 1
            if len(args) > 1:
                try:
                    amount = int(args[1])
                except ValueError:
                    return ["Training amount must be a number."]
            return loot.train_skill(state, skill_name, amount)

        if command == "talk":
            if not args:
                return ["Talk to whom? Example: talk wise old man"]
            return exploration.talk(state, " ".join(args))

        if command == "quest":
            objective = quest.get_current_objective(state)
            return [ui.format_quest(objective["title"], objective["description"], objective["hint"])]

        if command == "quit":
            state.game_over = True
            return ["Game ended."]

        return [f"Unknown command: {command}. Type `help` for a command list."]

    def run(self, state: GameState) -> None:
        """Run the command loop until quit."""
        self._clear_terminal()
        self.output_fn(ui.banner())
        self._emit_action([*exploration.look(state), "Type `help` for commands."])

        while not state.game_over:
            self._emit_lines(self._build_input_hints(state))
            try:
                raw = self.input_fn("> ")
            except EOFError:
                state.game_over = True
                break

            command, args = parse_command(raw)
            if not command:
                continue

            self._clear_terminal()
            action_messages = self._resolve_turn(state, command, args)
            self._emit_action(action_messages)
