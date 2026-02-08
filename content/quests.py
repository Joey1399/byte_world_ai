"""Quest stage metadata for byte_world_ai."""

from __future__ import annotations

from typing import Dict, List


QUEST_ORDER: List[str] = [
    "awakening",
    "swamp_secret",
    "mountain_flame",
    "castle_road",
    "black_hall",
    "witch_bane",
    "rescue_elle",
    "homecoming",
]


QUEST_STAGES: Dict[str, dict] = {
    "awakening": {
        "title": "Awakening",
        "description": "Meet the Wise Old Man in the Old Shack and learn what must be done.",
        "hint": "Use `talk wise old man` if you have not spoken to him.",
    },
    "swamp_secret": {
        "title": "The Swamp Secret",
        "description": "Travel to the swamp and defeat the Giant Frog.",
        "hint": "Forest creatures can be farmed for skill points before the boss.",
    },
    "mountain_flame": {
        "title": "Ash on the Peak",
        "description": "Climb Dragon Mountain, defeat the dragon, and claim its relics.",
        "hint": "The cave is optional, but dangerous treasure waits there.",
    },
    "castle_road": {
        "title": "Road of Knives",
        "description": "Survive the desolate road and deal with the Army of Goblins.",
        "hint": "You may joke, bribe, or fight.",
    },
    "black_hall": {
        "title": "King in Rot",
        "description": "Enter Makor's keep and defeat King Makor in the dungeon.",
        "hint": "The mysterious ring awakens when the fight turns desperate.",
    },
    "witch_bane": {
        "title": "Break the Curse",
        "description": "Defeat the Onyx Witch. Her black magic must be countered.",
        "hint": "The goblin riddle can break her binding spell.",
    },
    "rescue_elle": {
        "title": "Rescue Elle",
        "description": "Free Elle with the crusty key and cleanse her corruption with the vial.",
        "hint": "Use `use crusty key` and `use vial of tears` at the Witch's Terrace.",
    },
    "homecoming": {
        "title": "Homecoming",
        "description": "Elle is free and the corruption is gone. The journey is complete.",
        "hint": "Talk to Elle or the Wise Old Man for closing dialogue.",
    },
}

