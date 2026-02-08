"""World map and NPC content for byte_world_ai."""

from __future__ import annotations

from typing import Dict

from content.enemies import AREA_ENCOUNTER_TABLES


LOCATIONS: Dict[str, dict] = {
    "old_shack": {
        "name": "Old Shack",
        "area": "Forest of Magic",
        "descriptions": [
            "A leaning shack creaks in the wind. Candlelight flickers around old maps.",
            "The Wise Old Man's shack smells of herbs, smoke, and wet soil.",
        ],
        "exits": {"east": "forest"},
        "encounter_chance": 0.28,
        "encounters": AREA_ENCOUNTER_TABLES["old_shack"],
        "skill_points_per_kill": 1,
        "sense_hint": "You hear quiet muttering from inside the shack, and soft scratching outside.",
        "npcs": ["wise_old_man"],
    },
    "forest": {
        "name": "Forest",
        "area": "Forest of Magic",
        "descriptions": [
            "Thick trees bend over a narrow path cut by old boots and claws.",
            "Mist hangs low between roots. Every branch creak sounds like footsteps.",
        ],
        "exits": {"west": "old_shack", "east": "swamp", "south": "underground_tunnel", "north": "mountain_base"},
        "exit_requirements": {
            "north": {
                "all_flags": ["frog_defeated"],
                "message": "The mountain trail feels wrong. You should settle the swamp first.",
            }
        },
        "encounter_chance": 0.48,
        "encounters": AREA_ENCOUNTER_TABLES["forest"],
        "skill_points_per_kill": 2,
        "sense_hint": "Water stench drifts from the east, while cold mountain air leaks from the north.",
    },
    "swamp": {
        "name": "Swamp",
        "area": "Forest of Magic",
        "descriptions": [
            "Black water bubbles around rotted trees and broken reeds.",
            "The swamp is silent except for distant croaks that sound almost human.",
        ],
        "exits": {"west": "forest"},
        "encounter_chance": 0.0,
        "encounters": [],
        "boss_id": "giant_frog",
        "boss_flag": "frog_defeated",
        "sense_hint": "Something heavy moves beneath the water.",
    },
    "underground_tunnel": {
        "name": "Underground Tunnel",
        "area": "Forest of Magic",
        "descriptions": [
            "Packed earth walls squeeze around a tunnel lined with claw marks.",
            "Loose stones shift under your boots in the stale underground air.",
        ],
        "exits": {"north": "forest"},
        "encounter_chance": 0.52,
        "encounters": AREA_ENCOUNTER_TABLES["underground_tunnel"],
        "skill_points_per_kill": 3,
        "sense_hint": "You hear digging farther in, like a drumbeat through dirt.",
    },
    "mountain_base": {
        "name": "Dragon Mountain Base",
        "area": "Dragon Mountain",
        "descriptions": [
            "Steep cliffs rise ahead as embers drift down from somewhere above.",
            "Broken pillars and charred shrubs mark the mountain foothills.",
        ],
        "exits": {"south": "forest", "east": "abandoned_mine", "north": "mountain_peak", "west": "desolate_road"},
        "exit_requirements": {
            "west": {
                "all_flags": ["dragon_defeated"],
                "message": "A dreadful road calls to Makor's Castle. You are not ready yet.",
            }
        },
        "encounter_chance": 0.56,
        "encounters": AREA_ENCOUNTER_TABLES["mountain_base"],
        "skill_points_per_kill": 4,
        "sense_hint": "Heat washes down from the peak, but a dead stillness sits to the west.",
    },
    "abandoned_mine": {
        "name": "Abandoned Mine",
        "area": "Dragon Mountain",
        "descriptions": [
            "Collapsed rails and black ore veins cut through the cavern walls.",
            "Lantern hooks swing empty above a mine swallowed by ash.",
        ],
        "exits": {"west": "mountain_base"},
        "encounter_chance": 0.62,
        "encounters": AREA_ENCOUNTER_TABLES["abandoned_mine"],
        "skill_points_per_kill": 5,
        "sense_hint": "You hear scraping picks and hoarse whispers from deeper shafts.",
    },
    "mountain_peak": {
        "name": "Dragon Mountain Peak",
        "area": "Dragon Mountain",
        "descriptions": [
            "The summit is a ring of cracked stone and ancient bones.",
            "Winds scream across the peak, carrying ash and old warnings.",
        ],
        "exits": {"south": "mountain_base", "east": "mountain_cave"},
        "exit_requirements": {
            "east": {
                "all_flags": ["dragon_defeated"],
                "message": "The cave path is sealed by heat and rubble while the dragon lives.",
            }
        },
        "encounter_chance": 0.0,
        "encounters": [],
        "boss_id": "dragon",
        "boss_flag": "dragon_defeated",
        "sense_hint": "A shadow circles above, then vanishes in cloud.",
    },
    "mountain_cave": {
        "name": "Dragon Mountain Cave",
        "area": "Dragon Mountain",
        "descriptions": [
            "Gold glints between stalagmites under a low, rumbling growl.",
            "The cave floor is buried in coins, armor, and splintered bones.",
        ],
        "exits": {"west": "mountain_peak"},
        "encounter_chance": 0.0,
        "encounters": [],
        "boss_id": "ogre",
        "boss_flag": "ogre_defeated",
        "boss_optional": True,
        "boss_require_flags": ["dragon_defeated"],
        "sense_hint": "Treasure shines in the dark, but something bigger breathes nearby.",
    },
    "desolate_road": {
        "name": "Desolate Road",
        "area": "Makor's Castle",
        "descriptions": [
            "A dead road of cracked stone runs toward distant castle towers.",
            "No birds fly here. Only old battle standards flap in torn strips.",
        ],
        "exits": {"east": "mountain_base", "west": "royal_yard"},
        "encounter_chance": 0.52,
        "encounters": AREA_ENCOUNTER_TABLES["desolate_road"],
        "skill_points_per_kill": 6,
        "boss_id": "goblin_army",
        "boss_flag": "goblin_army_defeated",
        "boss_require_flags": ["dragon_defeated"],
        "sense_hint": "You spot tiny shadows shifting along the road walls.",
    },
    "royal_yard": {
        "name": "Royal Yard",
        "area": "Makor's Castle",
        "descriptions": [
            "Shattered statues and rusted spears fill the yard before the black keep.",
            "The ground is pitted with old fire and fresh blood.",
        ],
        "exits": {"east": "desolate_road", "north": "black_hall"},
        "exit_requirements": {
            "north": {
                "any_flags": ["goblin_army_defeated", "goblin_pass_granted"],
                "message": "You should survive the road's goblin ambush before entering the keep.",
            }
        },
        "encounter_chance": 0.6,
        "encounters": AREA_ENCOUNTER_TABLES["royal_yard"],
        "skill_points_per_kill": 7,
        "sense_hint": "A hollow laugh echoes from inside the keep.",
    },
    "black_hall": {
        "name": "Black Hall",
        "area": "Makor's Castle",
        "descriptions": [
            "Columns vanish into darkness while red torchlight stains the stone.",
            "The hall is empty, but a pulse beats behind the walls.",
        ],
        "exits": {"south": "royal_yard", "down": "dungeon", "north": "witch_terrace"},
        "exit_requirements": {
            "north": {
                "all_flags": ["makor_defeated"],
                "message": "A wall of pressure blocks the terrace stairs. Makor still stands.",
            }
        },
        "encounter_chance": 0.0,
        "encounters": [],
        "sense_hint": "Two red points flare in the dark, then blink out.",
    },
    "dungeon": {
        "name": "Dungeon",
        "area": "Makor's Castle",
        "descriptions": [
            "Iron bars and wet stone frame a pit beneath the castle.",
            "Chains drag across the floor as if pulled by unseen hands.",
        ],
        "exits": {"up": "black_hall"},
        "encounter_chance": 0.0,
        "encounters": [],
        "boss_id": "king_makor",
        "boss_flag": "makor_defeated",
        "sense_hint": "A blade scrapes against stone nearby.",
    },
    "witch_terrace": {
        "name": "Witch's Terrace",
        "area": "Makor's Castle",
        "descriptions": [
            "An open terrace hangs over a black void with runes carved in circles.",
            "Cold wind whips around a ritual platform stained with shadow.",
        ],
        "exits": {"south": "black_hall"},
        "encounter_chance": 0.0,
        "encounters": [],
        "boss_id": "onyx_witch",
        "boss_flag": "onyx_witch_defeated",
        "sense_hint": "You hear a woman sobbing between ritual chants.",
        "npcs": ["elle"],
    },
}


NPCS: Dict[str, dict] = {
    "wise_old_man": {
        "name": "Wise Old Man",
        "location_id": "old_shack",
        "first_dialogue": [
            "The old man lowers his hood and studies you.",
            "\"Three paths define survival: strike true, guard well, and harden your life.\"",
            "\"The swamp holds what was hidden. The mountain guards what was stolen.\"",
            "\"Listen to roads and ruins. They whisper before they kill.\"",
            "You learn combat skill: Focus Strike.",
        ],
        "repeat_dialogue": [
            "\"The key in the swamp opens more than doors.\"",
            "\"If goblins laugh, they may spare you. If they fear you, they may bargain.\"",
            "\"Do not trust victory over Makor to be the end.\"",
        ],
    },
    "elle": {
        "name": "Elle",
        "location_id": "witch_terrace",
        "first_dialogue": [
            "Elle rubs her wrists where shackles once held her.",
            "\"I knew someone would come, but not you.\"",
        ],
        "repeat_dialogue": [
            "\"The witch's corruption still burns in me... maybe the vial can purge it.\"",
        ],
        "cleansed_dialogue": [
            "Silver light leaves Elle's eyes as the corruption fades.",
            "\"It is over. Let's go home.\"",
        ],
    },
}
