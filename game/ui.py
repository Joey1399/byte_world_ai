"""Rendering helpers for byte_world_ai CLI output."""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path
from typing import Dict, Iterable, List

from content.enemies import ENEMIES
from content.items import ITEMS
from content.world import NPCS


DIVIDER = "-" * 64
ACTION_SEPARATOR = "=" * 64
_TITLE_TEXT_PATH = Path(__file__).resolve().parents[1] / "content" / "ascii" / "title_text.txt"
_TITLE_TEXT_FALLBACK = "byte_world_ai :: CLI adventure"

ANSI_RESET = "\033[0m"
ANSI_BLUE = "\033[38;5;39m"
ANSI_YELLOW = "\033[93m"
ANSI_ORANGE = "\033[38;5;208m"
ANSI_RED = "\033[91m"
ANSI_HEALTH_GREEN = "\033[38;5;82m"
ANSI_ITEM_GREEN = "\033[38;5;120m"
ANSI_PURPLE = "\033[95m"
ANSI_PINK = "\033[38;5;213m"

_END_BOSS_IDS = {"king_makor", "onyx_witch"}
_IMPORTANT_OR_RARE_ITEM_IDS = {
    "crusty_key",
    "mysterious_ring",
    "goblin_riddle",
    "makor_soul",
    "vial_of_tears",
    "hoard_treasure",
    "dragon_ring",
    "moonbite_dagger",
    "echo_plate",
    "warding_totem",
    "skill_cache_10",
    "skill_cache_20",
    "skill_cache_30",
}


def _enable_windows_ansi() -> None:
    """Enable ANSI color support on Windows terminals that need it."""
    if os.name != "nt":
        return
    try:
        import ctypes

        kernel32 = ctypes.windll.kernel32
        handle = kernel32.GetStdHandle(-11)  # STD_OUTPUT_HANDLE
        mode = ctypes.c_uint()
        if kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
            kernel32.SetConsoleMode(handle, mode.value | 0x0004)  # ENABLE_VIRTUAL_TERMINAL_PROCESSING
    except Exception:
        # Fallback to plain text if terminal APIs are unavailable.
        pass


_enable_windows_ansi()
_FORCE_COLOR = os.getenv("BYTE_WORLD_AI_FORCE_COLOR") == "1" or os.getenv("BYTE_WORLD_FORCE_COLOR") == "1"
_COLOR_ENABLED = os.getenv("NO_COLOR") is None and (sys.stdout.isatty() or _FORCE_COLOR)


def _paint(text: str, color_code: str) -> str:
    if not _COLOR_ENABLED:
        return text
    return f"{color_code}{text}{ANSI_RESET}"


def _compile_name_pattern(names: Iterable[str]) -> re.Pattern[str] | None:
    filtered = [name for name in names if name]
    if not filtered:
        return None
    escaped = sorted((re.escape(name) for name in filtered), key=len, reverse=True)
    return re.compile(r"(?<!\w)(" + "|".join(escaped) + r")(?!\w)", re.IGNORECASE)


def _item_is_purple(item_id: str, item: dict) -> bool:
    if item_id in _IMPORTANT_OR_RARE_ITEM_IDS:
        return True
    return item.get("type") in {"quest", "key", "boon"}


_NPC_NAMES = {npc.get("name", "") for npc in NPCS.values()}
_CREATURE_NAMES = {
    enemy.get("name", "")
    for enemy_id, enemy in ENEMIES.items()
    if enemy.get("category") == "normal"
}
_BOSS_NAMES = {
    enemy.get("name", "")
    for enemy_id, enemy in ENEMIES.items()
    if enemy.get("category") == "boss" and enemy_id not in _END_BOSS_IDS
}
_END_BOSS_NAMES = {ENEMIES[enemy_id].get("name", "") for enemy_id in _END_BOSS_IDS if enemy_id in ENEMIES}
_PURPLE_ITEM_NAMES = {
    item.get("name", "")
    for item_id, item in ITEMS.items()
    if _item_is_purple(item_id, item)
}
_GREEN_ITEM_NAMES = {
    item.get("name", "")
    for item_id, item in ITEMS.items()
    if not _item_is_purple(item_id, item)
}
_SKILL_TERMS = {
    "attack",
    "defense",
    "health",
    "focus strike",
    "guard stance",
    "second wind",
}

_COLOR_PATTERNS: list[tuple[re.Pattern[str] | None, str]] = [
    (_compile_name_pattern(_END_BOSS_NAMES), ANSI_RED),
    (_compile_name_pattern(_BOSS_NAMES), ANSI_ORANGE),
    (_compile_name_pattern(_CREATURE_NAMES), ANSI_YELLOW),
    (_compile_name_pattern(_NPC_NAMES), ANSI_BLUE),
    (_compile_name_pattern(_SKILL_TERMS), ANSI_PINK),
    (_compile_name_pattern(_PURPLE_ITEM_NAMES), ANSI_PURPLE),
    (_compile_name_pattern(_GREEN_ITEM_NAMES), ANSI_ITEM_GREEN),
]


def _colorize_interactables(text: str) -> str:
    if not text:
        return text
    rendered = text
    for pattern, color in _COLOR_PATTERNS:
        if pattern is None:
            continue
        rendered = pattern.sub(lambda match: _paint(match.group(0), color), rendered)
    return rendered


def health_bar(current_hp: int, max_hp: int, width: int = 24) -> str:
    """Render an ASCII HP bar with green current HP and red missing HP."""
    max_hp = max(1, int(max_hp))
    current_hp = max(0, min(int(current_hp), max_hp))

    filled = int(round((current_hp / max_hp) * width))
    if current_hp > 0:
        filled = max(1, filled)
    filled = min(width, filled)
    empty = max(0, width - filled)

    fill_text = "#" * filled
    empty_text = "-" * empty

    if _COLOR_ENABLED:
        fill_text = _paint(fill_text, ANSI_HEALTH_GREEN) if fill_text else ""
        empty_text = _paint(empty_text, ANSI_RED) if empty_text else ""

    return f"[{fill_text}{empty_text}] {current_hp}/{max_hp}"


def combat_health_lines(
    player_hp: int,
    player_max_hp: int,
    enemy_name: str,
    enemy_hp: int,
    enemy_max_hp: int,
) -> list[str]:
    """Return player/enemy HP bars for combat log output."""
    return [
        "HP:",
        f"  You: {health_bar(player_hp, player_max_hp)}",
        f"  {enemy_name}: {health_bar(enemy_hp, enemy_max_hp)}",
    ]


def _clip_label(text: str, max_len: int = 40) -> str:
    if len(text) <= max_len:
        return text
    return text[: max_len - 3] + "..."


def format_world_map(current_location_name: str, direction_labels: dict[str, str], route_lines: list[str]) -> str:
    """Render a simple local directional map."""
    north = _clip_label(direction_labels.get("north", "---"))
    south = _clip_label(direction_labels.get("south", "---"))
    east = _clip_label(direction_labels.get("east", "---"))
    west = _clip_label(direction_labels.get("west", "---"))
    up = _clip_label(direction_labels.get("up", "---"))
    down = _clip_label(direction_labels.get("down", "---"))

    lines = [
        DIVIDER,
        "Map",
        f"You are at: [YOU] {current_location_name}",
        "",
        f"              {north}",
        "                ^",
        "                |",
        f"{west}  <- [YOU] ->  {east}",
        "                |",
        "                v",
        f"              {south}",
        "",
        f"Up: {up}",
        f"Down: {down}",
    ]

    if route_lines:
        lines.append("")
        lines.append("Quick direction guide:")
        for route in route_lines:
            lines.append(f"  - {route}")

    return "\n".join(lines)


def banner() -> str:
    title_text = _TITLE_TEXT_FALLBACK
    for candidate in (_TITLE_TEXT_PATH, Path("content/ascii/title_text.txt")):
        try:
            loaded = candidate.read_text(encoding="utf-8")
        except OSError:
            continue
        normalized = loaded.replace("\r\n", "\n").replace("\r", "\n").strip("\n")
        if normalized.strip():
            title_text = normalized
            break

    return "\n".join(
        [
            DIVIDER,
            title_text,
            DIVIDER,
        ]
    )


def help_text() -> str:
    rows = [
        ("system", "help", "Show this command menu."),
        ("system", "quit", "Exit the game."),
        ("info", "status", "Show HP, stats, level, gold, and equipped gear."),
        ("info", "quest", "Show current quest objective and hint."),
        ("info", "look", "Describe your current location and exits."),
        ("info", "sense", "Show subtle hints about this area."),
        ("info", "map", "Show a directional map with your location and route hints."),
        ("explore", "hunt", "Force a creature encounter in areas that have roaming enemies."),
        ("explore", "move <dir>", "Travel north/south/east/west/up/down (n/s/e/w/u/d aliases)."),
        ("social", "talk <npc>", "Talk to a visible NPC in your current location."),
        ("gear", "inventory", "List items in your inventory."),
        ("gear", "equip <item>", "Equip a weapon, armor, shield, accessory, or aura."),
        ("gear", "equip all", "Auto-equip best-in-slot gear from inventory."),
        ("gear", "use <item>", "Use consumables or context items (key, vial, etc.)."),
        ("gear", "read <item>", "Read special items such as the goblin riddle."),
        ("progression", "train <stat> [pts]", "Spend skill points on attack, defense, or health."),
        ("progression", "train all", "Train attack/defense/health equally with available points."),
        ("progression", "train a,b,c", "Train exact split (attack, defense, health). Example: train 3,4,3."),
        ("combat", "fight", "Attack the active enemy."),
        ("combat", "defend", "Reduce next incoming hit."),
        ("combat", "skill <name>", "Use a learned skill (focus strike, guard stance, second wind)."),
        ("combat", "run", "Attempt to flee an encounter."),
        ("combat*", "joke", "Goblin army only: attempt peaceful escape."),
        ("combat*", "bribe", "Goblin army only: pay gold to avoid combat."),
    ]

    headers = ("group", "command", "description")
    group_w = max(len(headers[0]), *(len(row[0]) for row in rows))
    cmd_w = max(len(headers[1]), *(len(row[1]) for row in rows))
    desc_w = 62

    def clamp(text: str, width: int) -> str:
        if len(text) <= width:
            return text
        return text[: width - 3] + "..."

    top = "+" + "-" * (group_w + 2) + "+" + "-" * (cmd_w + 2) + "+" + "-" * (desc_w + 2) + "+"
    title_inner = group_w + cmd_w + desc_w + 8
    title = "| " + "byte_world_ai command menu".center(title_inner - 2) + " |"
    header = (
        f"| {headers[0].ljust(group_w)} | {headers[1].ljust(cmd_w)} | {headers[2].ljust(desc_w)} |"
    )

    lines = [top, title, top, header, top]
    for group, command, desc in rows:
        lines.append(
            f"| {group.ljust(group_w)} | {command.ljust(cmd_w)} | {clamp(desc, desc_w).ljust(desc_w)} |"
        )
    lines.append(top)
    lines.append("Notes:")
    lines.append("  - During encounters, movement/talk/train are blocked until you win, escape, or lose.")
    lines.append("  - `joke` and `bribe` are only valid during the goblin army negotiation phase.")
    lines.append("Color key:")
    lines.append(
        "  - "
        + ", ".join(
            [
                f"{_paint('NPC', ANSI_BLUE)} = talkable",
                f"{_paint('Creature', ANSI_YELLOW)} = fightable",
                f"{_paint('Boss', ANSI_ORANGE)} = boss fight",
                f"{_paint('End-boss', ANSI_RED)} = Makor / Witch",
                f"{_paint('Item', ANSI_ITEM_GREEN)} = item/equipment",
                f"{_paint('Rare/Quest', ANSI_PURPLE)} = rare or important reward",
                f"{_paint('Skill', ANSI_PINK)} = train/combat skill terms",
            ]
        )
    )
    return "\n".join(lines)


def format_location(location: dict, description: str) -> str:
    exits = ", ".join(sorted(location.get("exits", {}).keys())) or "none"
    lines = [
        DIVIDER,
        f"{location.get('name', 'Unknown')} [{location.get('area', 'Unknown')}]",
        description,
        f"Exits: {exits}",
    ]
    npc_ids = location.get("npcs", [])
    if npc_ids:
        npc_names = [NPCS.get(npc_id, {}).get("name", npc_id) for npc_id in npc_ids]
        lines.append(f"NPCs here: {', '.join(npc_names)}")
    return "\n".join(lines)


def format_status(status: dict) -> str:
    equipment = status["equipment"]
    equipped_text = ", ".join(f"{slot}:{item}" for slot, item in equipment.items())
    titles = ", ".join(status["titles"]) if status["titles"] else "none"
    hp_bar = health_bar(int(status["hp"]), int(status["max_hp"]))
    return "\n".join(
        [
            DIVIDER,
            f"{status['name']}  Level {status['level']}",
            f"HP: {status['hp']}/{status['max_hp']}  Attack: {status['attack']}  Defense: {status['defense']}",
            f"HP Bar: {hp_bar}",
            f"XP: {status['xp']}  Skill Points: {status['skill_points']}  Gold: {status['gold']}",
            f"Titles: {titles}",
            f"Equipped: {equipped_text}",
        ]
    )


def _item_stat_suffix(item: dict) -> str:
    parts: list[str] = []
    attack = int(item.get("attack_bonus", 0))
    defense = int(item.get("defense_bonus", 0))
    health = int(item.get("max_hp_bonus", 0))
    heal = int(item.get("heal_amount", 0))
    skill_points = int(item.get("skill_points_bonus", 0))

    if attack:
        parts.append(f"attack {attack:+d}")
    if defense:
        parts.append(f"defense {defense:+d}")
    if health:
        parts.append(f"health {health:+d}")
    if heal:
        parts.append(f"heal +{heal}")
    if skill_points:
        parts.append(f"skill points +{skill_points}")

    if not parts:
        return ""
    return " [" + ", ".join(parts) + "]"


def format_inventory(inventory: Dict[str, int]) -> str:
    if not inventory:
        return "Inventory is empty."
    lines = [DIVIDER, "Inventory:"]
    for item_id, qty in sorted(inventory.items()):
        item = ITEMS.get(item_id, {})
        name = item.get("name", item_id)
        item_type = item.get("type", "unknown")
        lines.append(f"  {name} x{qty} ({item_type}){_item_stat_suffix(item)}")
    return "\n".join(lines)


def format_messages(messages: Iterable[str]) -> str:
    formatted: list[str] = []
    for msg in messages:
        if not msg:
            continue
        formatted.append(_colorize_interactables(msg))
    return "\n".join(formatted)


def format_action_block(messages: Iterable[str]) -> str:
    """Render one command result as a visually separated CLI block."""
    body = format_messages(messages)
    if not body:
        return ""
    return "\n".join([ACTION_SEPARATOR, body, ACTION_SEPARATOR])


def format_encounter(enemy_name: str, enemy_hp: int, enemy_max_hp: int, intent: str) -> str:
    return "\n".join(
        [
            DIVIDER,
            f"Encounter: {enemy_name}",
            f"Enemy HP: {enemy_hp}/{enemy_max_hp}",
            f"Intent: {intent}",
        ]
    )


def format_quest(title: str, description: str, hint: str) -> str:
    return "\n".join(
        [
            DIVIDER,
            f"Quest: {title}",
            description,
            f"Hint: {hint}",
        ]
    )
