"""Quest stage tracking and progression checks."""

from __future__ import annotations

from typing import List

from content.quests import QUEST_STAGES
from game.state import GameState


def _determine_stage(state: GameState) -> str:
    if "met_old_man" not in state.flags:
        return "awakening"
    if "frog_defeated" not in state.flags:
        return "swamp_secret"
    if "dragon_defeated" not in state.flags:
        return "mountain_flame"
    if "goblin_army_defeated" not in state.flags and "goblin_pass_granted" not in state.flags:
        return "castle_road"
    if "makor_defeated" not in state.flags:
        return "black_hall"
    if "onyx_witch_defeated" not in state.flags:
        return "witch_bane"
    if "elle_cleansed" not in state.flags:
        return "rescue_elle"
    return "homecoming"


def check_and_advance(state: GameState) -> List[str]:
    """Advance quest stage based on current flags."""
    new_stage = _determine_stage(state)
    if new_stage == state.quest_stage:
        return []

    state.quest_stage = new_stage
    stage = QUEST_STAGES[new_stage]
    messages = [f"Quest updated: {stage['title']}", stage["description"]]

    if new_stage == "homecoming":
        state.victory = True

    return messages


def get_current_objective(state: GameState) -> dict:
    """Return the active quest stage object."""
    return QUEST_STAGES[state.quest_stage]

