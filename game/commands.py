"""Command parser for byte_world_ai CLI."""

from __future__ import annotations

from typing import List, Tuple


ALIASES = {
    "n": "move north",
    "s": "move south",
    "e": "move east",
    "w": "move west",
    "u": "move up",
    "d": "move down",
    "north": "move north",
    "south": "move south",
    "east": "move east",
    "west": "move west",
    "up": "move up",
    "down": "move down",
    "farm": "hunt",
    "grind": "hunt",
    "i": "inventory",
    "inv": "inventory",
    "q": "quit",
    "exit": "quit",
    "attack": "fight",
    "atk": "fight",
    "read": "read",
}


def parse_command(raw: str) -> Tuple[str, List[str]]:
    """Parse user input into (command, args)."""
    text = raw.strip().lower()
    if not text:
        return "", []

    if text in ALIASES:
        text = ALIASES[text]

    parts = text.split()
    if not parts:
        return "", []

    command = parts[0]
    args = parts[1:]
    return command, args
