"""Enemy and boss definitions for byte_world_ai."""

from __future__ import annotations

from typing import Dict, List


ENEMIES: Dict[str, dict] = {
    "rat": {
        "name": "Sewer Rat",
        "category": "normal",
        "hp": 14,
        "attack": 4,
        "defense": 1,
        "xp_reward": 8,
        "gold_reward": 4,
        "loot_table": [("sturdy_bandage", 35), ("minor_potion", 12)],
    },
    "wolf": {
        "name": "Forest Wolf",
        "category": "normal",
        "hp": 22,
        "attack": 7,
        "defense": 2,
        "xp_reward": 14,
        "gold_reward": 8,
        "loot_table": [("minor_potion", 18)],
    },
    "giant_mole": {
        "name": "Giant Mole",
        "category": "normal",
        "hp": 28,
        "attack": 8,
        "defense": 4,
        "xp_reward": 18,
        "gold_reward": 12,
        "loot_table": [("minor_potion", 20), ("patched_coat", 10)],
    },
    "whelp": {
        "name": "Mountain Whelp",
        "category": "normal",
        "hp": 35,
        "attack": 10,
        "defense": 4,
        "xp_reward": 24,
        "gold_reward": 16,
        "loot_table": [("minor_potion", 24)],
    },
    "corrupt_dwarf": {
        "name": "Corrupt Dwarf",
        "category": "normal",
        "hp": 42,
        "attack": 12,
        "defense": 6,
        "xp_reward": 30,
        "gold_reward": 22,
        "loot_table": [("minor_potion", 20), ("rusted_blade", 10)],
    },
    "goblin_squire": {
        "name": "Goblin Squire",
        "category": "normal",
        "hp": 48,
        "attack": 14,
        "defense": 7,
        "xp_reward": 36,
        "gold_reward": 26,
        "loot_table": [("minor_potion", 16)],
    },
    "corrupted_knight": {
        "name": "Corrupted Knight",
        "category": "normal",
        "hp": 56,
        "attack": 16,
        "defense": 9,
        "xp_reward": 42,
        "gold_reward": 32,
        "loot_table": [("minor_potion", 20), ("patched_coat", 6)],
    },
    "giant_frog": {
        "name": "Giant Frog, Prince of the Swamp",
        "category": "boss",
        "hp": 85,
        "attack": 13,
        "defense": 6,
        "xp_reward": 80,
        "gold_reward": 55,
        "skill_points_reward": 6,
        "guaranteed_drops": ["crusty_key", "crusty_sword", "froghide_armor"],
        "pre_dialogue": [
            "The swamp bubbles and a giant frog rises from the black water.",
            "\"I am the Prince of this swamp. A dark secret sleeps inside me.\"",
        ],
        "post_dialogue": [
            "The prince collapses into the mud.",
            "You pry a crusty key from the corpse.",
            "A whisper crosses the water: the Onyx Witch hid this key far away, and the frog swallowed it.",
        ],
        "intents": [
            {
                "name": "Tongue Lash",
                "telegraph": "The frog coils its tongue like a spring.",
                "base_damage": 12,
                "defend_multiplier": 0.4,
            },
            {
                "name": "Bog Burst",
                "telegraph": "Its throat glows green as swamp gas gathers.",
                "base_damage": 16,
                "defend_multiplier": 0.25,
            },
        ],
    },
    "dragon": {
        "name": "Ash Dragon",
        "category": "boss",
        "hp": 130,
        "attack": 19,
        "defense": 10,
        "xp_reward": 140,
        "gold_reward": 95,
        "skill_points_reward": 10,
        "guaranteed_drops": [
            "mysterious_ring",
            "dragon_armor",
            "obsidian_amulet",
            "obsidian_scimitar",
        ],
        "pre_dialogue": [
            "At the peak, a dragon lands on ancient bones with a hiss.",
            "\"No one survives this summit. Not even Makor's oldest son.\"",
        ],
        "post_dialogue": [
            "The dragon turns to drifting ash.",
            "An echo rides the wind: \"Treasure waits in the cave, but peril owns it.\"",
        ],
        "intents": [
            {
                "name": "Cinder Breath",
                "telegraph": "Flames gather in the dragon's chest.",
                "base_damage": 20,
                "defend_multiplier": 0.35,
            },
            {
                "name": "Tail Reap",
                "telegraph": "Its tail carves a wide arc through the air.",
                "base_damage": 17,
                "defend_multiplier": 0.5,
            },
            {
                "name": "Sky Dive",
                "telegraph": "The dragon launches upward, shadow swallowing the ground.",
                "base_damage": 24,
                "defend_multiplier": 0.3,
            },
        ],
    },
    "ogre": {
        "name": "Hoard Ogre",
        "category": "boss",
        "hp": 150,
        "attack": 21,
        "defense": 11,
        "xp_reward": 160,
        "gold_reward": 120,
        "skill_points_reward": 12,
        "guaranteed_drops": ["hoard_treasure", "dragon_ring", "dragon_shield"],
        "pre_dialogue": [
            "A hulking ogre stomps out of the treasure cave.",
            "\"Leave now or die. This hoard is mine.\"",
        ],
        "post_dialogue": [
            "The ogre slumps over the treasure.",
            "\"Take... the hoard... back to the old man...\"",
        ],
        "intents": [
            {
                "name": "Boulder Crush",
                "telegraph": "The ogre raises a boulder over its head.",
                "base_damage": 22,
                "defend_multiplier": 0.35,
            },
            {
                "name": "Ground Slam",
                "telegraph": "It digs both feet in, preparing a shockwave.",
                "base_damage": 19,
                "defend_multiplier": 0.45,
            },
        ],
    },
    "goblin_army": {
        "name": "Army of Goblins",
        "category": "boss",
        "hp": 165,
        "attack": 18,
        "defense": 9,
        "xp_reward": 170,
        "gold_reward": 130,
        "skill_points_reward": 14,
        "guaranteed_drops": ["goblin_riddle"],
        "pre_dialogue": [
            "Ropes snap tight around your arms as goblins surround you.",
            "\"Traveling near Makor's Castle? Brave... and stupid.\"",
            "You can try `joke`, `bribe`, or `fight`.",
        ],
        "post_dialogue": [
            "Most of the goblins fall. One survivor throws you a scrap of parchment.",
            "\"Take it! A riddle to break the witch's curse. Just let me live.\"",
        ],
        "intents": [
            {
                "name": "Mob Rush",
                "telegraph": "The front rank lowers spears and stamps forward.",
                "base_damage": 18,
                "defend_multiplier": 0.45,
            },
            {
                "name": "Javelin Volley",
                "telegraph": "A rain of crude javelins rises into the sky.",
                "base_damage": 21,
                "defend_multiplier": 0.35,
            },
        ],
        "special": "goblin_negotiation",
    },
    "king_makor": {
        "name": "King Makor the Rot",
        "category": "boss",
        "hp": 190,
        "attack": 25,
        "defense": 13,
        "xp_reward": 220,
        "gold_reward": 160,
        "skill_points_reward": 18,
        "guaranteed_drops": ["makor_soul"],
        "pre_dialogue": [
            "A voice booms through the Black Hall: \"So this is the one Elle mentioned.\"",
            "Red eyes ignite in darkness and then your vision goes black.",
            "You wake in a dungeon cell. Makor laughs, certain you are weak.",
            "Your hand finds the mysterious ring. It burns with sudden power.",
        ],
        "post_dialogue": [
            "Makor drops to one knee and begs forgiveness.",
            "You strike anyway. His final scream echoes: \"You'll never defeat her!\"",
            "His body collapses into dust.",
        ],
        "intents": [
            {
                "name": "Rot Blade",
                "telegraph": "Makor draws a blackened blade dripping shadow.",
                "base_damage": 25,
                "defend_multiplier": 0.4,
            },
            {
                "name": "Soul Rend",
                "telegraph": "Dark sigils spiral around Makor's gauntlet.",
                "base_damage": 28,
                "defend_multiplier": 0.35,
            },
            {
                "name": "Crushing Lunge",
                "telegraph": "He crouches low, preparing to cross the room in one leap.",
                "base_damage": 23,
                "defend_multiplier": 0.45,
            },
        ],
    },
    "onyx_witch": {
        "name": "The Onyx Witch",
        "category": "boss",
        "hp": 230,
        "attack": 29,
        "defense": 16,
        "xp_reward": 300,
        "gold_reward": 200,
        "skill_points_reward": 22,
        "guaranteed_drops": ["vial_of_tears"],
        "pre_dialogue": [
            "The witch drags Elle forward in chains and smiles.",
            "\"Makor was weak. You are weaker.\"",
            "Black magic coils around your limbs. You cannot strike.",
            "Try `read riddle` when the time is right.",
        ],
        "post_dialogue": [
            "The witch's soul collapses inward and vanishes beneath the stone.",
            "A thousand-voice scream rises and then cuts to silence.",
        ],
        "intents": [
            {
                "name": "Curse Pulse",
                "telegraph": "Black runes flare across the terrace floor.",
                "base_damage": 24,
                "defend_multiplier": 0.45,
            },
            {
                "name": "Void Lance",
                "telegraph": "She forms a spear of onyx light in her palm.",
                "base_damage": 30,
                "defend_multiplier": 0.3,
            },
            {
                "name": "Blood Hex",
                "telegraph": "Her voice drops to a whisper as your pulse stutters.",
                "base_damage": 26,
                "defend_multiplier": 0.4,
            },
        ],
        "special": "witch_barrier",
    },
}


_BASE_ENEMY_BY_LOCATION: Dict[str, str] = {
    "old_shack": "rat",
    "forest": "wolf",
    "underground_tunnel": "giant_mole",
    "mountain_base": "whelp",
    "abandoned_mine": "corrupt_dwarf",
    "desolate_road": "goblin_squire",
    "royal_yard": "corrupted_knight",
}


_LOCATION_CREATURE_VARIANTS: Dict[str, List[tuple[str, str]]] = {
    "old_shack": [
        ("cellar_rat", "Cellar Rat"),
        ("attic_rat", "Attic Rat"),
        ("needle_mouse", "Needle Mouse"),
        ("splinter_mouse", "Splinter Mouse"),
        ("mold_mite_swarm", "Mold Mite Swarm"),
        ("soot_lizard", "Soot Lizard"),
        ("root_gecko", "Root Gecko"),
        ("bog_tick_cluster", "Bog Tick Cluster"),
        ("scrap_beetle", "Scrap Beetle"),
        ("shack_spider", "Shack Spider"),
        ("thorn_snail", "Thorn Snail"),
        ("gutter_newt", "Gutter Newt"),
        ("splint_crow", "Splint Crow"),
        ("moss_crab", "Moss Crab"),
        ("burrow_flea_pack", "Burrow Flea Pack"),
        ("lantern_moth", "Lantern Moth"),
        ("mud_slug", "Mud Slug"),
        ("hollow_weasel", "Hollow Weasel"),
        ("woodworm_hive", "Woodworm Hive"),
    ],
    "forest": [
        ("briar_wolf", "Briar Wolf"),
        ("feral_fox", "Feral Fox"),
        ("thorn_boar", "Thorn Boar"),
        ("bark_serpent", "Bark Serpent"),
        ("shade_hare", "Shade Hare"),
        ("vine_panther", "Vine Panther"),
        ("iron_ant_swarm", "Iron Ant Swarm"),
        ("mist_stag", "Mist Stag"),
        ("bramble_lurker", "Bramble Lurker"),
        ("hollow_hound", "Hollow Hound"),
        ("ivy_mantis", "Ivy Mantis"),
        ("root_tortoise", "Root Tortoise"),
        ("crow_hexer", "Crow Hexer"),
        ("moss_lynx", "Moss Lynx"),
        ("glade_viper", "Glade Viper"),
        ("antler_fiend", "Antler Fiend"),
        ("fungus_ape", "Fungus Ape"),
        ("dusk_howler", "Dusk Howler"),
        ("fern_stalker", "Fern Stalker"),
    ],
    "underground_tunnel": [
        ("tunnel_mole", "Tunnel Mole"),
        ("stone_mole", "Stone Mole"),
        ("cave_rat_alpha", "Cave Rat Alpha"),
        ("burrow_serpent", "Burrow Serpent"),
        ("cave_spider", "Cave Spider"),
        ("blind_bat_swarm", "Blind Bat Swarm"),
        ("shale_beetle", "Shale Beetle"),
        ("tunnel_ghoul", "Tunnel Ghoul"),
        ("mud_golemlet", "Mud Golemlet"),
        ("ore_maggot_swarm", "Ore Maggot Swarm"),
        ("tremor_worm", "Tremor Worm"),
        ("rust_mole", "Rust Mole"),
        ("echo_bat", "Echo Bat"),
        ("cavern_newt", "Cavern Newt"),
        ("dirt_wraith", "Dirt Wraith"),
        ("slag_crab", "Slag Crab"),
        ("granite_tunneler", "Granite Tunneler"),
        ("hollow_digger", "Hollow Digger"),
        ("sinkhole_leech", "Sinkhole Leech"),
    ],
    "mountain_base": [
        ("ash_whelp", "Ash Whelp"),
        ("ember_whelp", "Ember Whelp"),
        ("cliff_harpy", "Cliff Harpy"),
        ("basalt_ram", "Basalt Ram"),
        ("cinder_imp", "Cinder Imp"),
        ("smoke_serpent", "Smoke Serpent"),
        ("crag_stalker", "Crag Stalker"),
        ("magma_hound", "Magma Hound"),
        ("ash_scorpid", "Ash Scorpid"),
        ("lava_lizard", "Lava Lizard"),
        ("ember_hawk", "Ember Hawk"),
        ("stone_gargoyle", "Stone Gargoyle"),
        ("ember_mantis", "Ember Mantis"),
        ("soot_tiger", "Soot Tiger"),
        ("cliff_wyvernling", "Cliff Wyvernling"),
        ("charred_boar", "Charred Boar"),
        ("hotwind_spirit", "Hotwind Spirit"),
        ("flint_ogrekin", "Flint Ogrekin"),
        ("blaze_wolf", "Blaze Wolf"),
    ],
    "abandoned_mine": [
        ("mine_wraith", "Mine Wraith"),
        ("pickaxe_ghoul", "Pickaxe Ghoul"),
        ("ore_spider", "Ore Spider"),
        ("cursed_miner", "Cursed Miner"),
        ("ash_bat_swarm", "Ash Bat Swarm"),
        ("lantern_specter", "Lantern Specter"),
        ("slag_hound", "Slag Hound"),
        ("vein_serpent", "Vein Serpent"),
        ("iron_golemlet", "Iron Golemlet"),
        ("dust_imp", "Dust Imp"),
        ("collapse_beetle", "Collapse Beetle"),
        ("soot_dwarf", "Soot Dwarf"),
        ("chain_revenant", "Chain Revenant"),
        ("coal_mimic", "Coal Mimic"),
        ("crystal_lurker", "Crystal Lurker"),
        ("tunnel_fiend", "Tunnel Fiend"),
        ("drill_mole", "Drill Mole"),
        ("shaft_stalker", "Shaft Stalker"),
        ("blast_bomber", "Blast Bomber"),
    ],
    "desolate_road": [
        ("goblin_raider", "Goblin Raider"),
        ("goblin_archer", "Goblin Archer"),
        ("goblin_skirmisher", "Goblin Skirmisher"),
        ("goblin_bruiser", "Goblin Bruiser"),
        ("goblin_shaman", "Goblin Shaman"),
        ("goblin_bombardier", "Goblin Bombardier"),
        ("goblin_wolf_rider", "Goblin Wolf Rider"),
        ("goblin_pikeman", "Goblin Pikeman"),
        ("goblin_duelist", "Goblin Duelist"),
        ("goblin_reaver", "Goblin Reaver"),
        ("goblin_scout", "Goblin Scout"),
        ("goblin_juggernaut", "Goblin Juggernaut"),
        ("goblin_pyro", "Goblin Pyro"),
        ("goblin_hexer", "Goblin Hexer"),
        ("goblin_banneret", "Goblin Banneret"),
        ("goblin_ambusher", "Goblin Ambusher"),
        ("goblin_sapper", "Goblin Sapper"),
        ("goblin_warlock", "Goblin Warlock"),
        ("goblin_veteran", "Goblin Veteran"),
    ],
    "royal_yard": [
        ("corrupted_sentinel", "Corrupted Sentinel"),
        ("corrupted_halberdier", "Corrupted Halberdier"),
        ("cursed_arbalist", "Cursed Arbalist"),
        ("blood_guard", "Blood Guard"),
        ("black_lancer", "Black Lancer"),
        ("iron_watcher", "Iron Watcher"),
        ("shade_templar", "Shade Templar"),
        ("hollow_paladin", "Hollow Paladin"),
        ("dusk_executioner", "Dusk Executioner"),
        ("blight_captain", "Blight Captain"),
        ("grave_warden", "Grave Warden"),
        ("scarlet_marshal", "Scarlet Marshal"),
        ("ruin_champion", "Ruin Champion"),
        ("void_squire", "Void Squire"),
        ("oathbreaker_knight", "Oathbreaker Knight"),
        ("chain_knight", "Chain Knight"),
        ("soul_bastion", "Soul Bastion"),
        ("fallen_duke", "Fallen Duke"),
        ("dread_cavalier", "Dread Cavalier"),
    ],
}


def _build_variant_enemy(base_enemy: dict, name: str, index: int) -> dict:
    """Derive balanced normal-enemy variants from a location baseline enemy."""
    hp = int(base_enemy["hp"]) + index * 2
    attack = int(base_enemy["attack"]) + int((index + 2) / 4)
    defense = int(base_enemy["defense"]) + int((index + 3) / 6)
    xp_reward = int(base_enemy.get("xp_reward", 0)) + index * 2
    gold_reward = int(base_enemy.get("gold_reward", 0)) + index * 2
    loot_table = list(base_enemy.get("loot_table", []))
    return {
        "name": name,
        "category": "normal",
        "hp": hp,
        "attack": attack,
        "defense": defense,
        "xp_reward": xp_reward,
        "gold_reward": gold_reward,
        "loot_table": loot_table,
    }


def _register_location_creatures() -> Dict[str, List[tuple[str, int]]]:
    """Attach 19 variants per farm location and expose 20-creature encounter tables."""
    encounter_tables: Dict[str, List[tuple[str, int]]] = {}

    for location_id, base_enemy_id in _BASE_ENEMY_BY_LOCATION.items():
        base_enemy = ENEMIES[base_enemy_id]
        variants = _LOCATION_CREATURE_VARIANTS[location_id]
        encounter_ids = [base_enemy_id]

        for index, (enemy_id, enemy_name) in enumerate(variants, start=1):
            ENEMIES[enemy_id] = _build_variant_enemy(base_enemy, enemy_name, index)
            encounter_ids.append(enemy_id)

        encounter_tables[location_id] = [(enemy_id, 1) for enemy_id in encounter_ids]

    return encounter_tables


AREA_ENCOUNTER_TABLES: Dict[str, List[tuple[str, int]]] = _register_location_creatures()


RARITY_TABLES: Dict[str, List[tuple[str, int]]] = {
    "common_field": [
        ("moonbite_dagger", 16),
        ("echo_plate", 14),
        ("warding_totem", 12),
        ("obsidian_amulet", 8),
        ("dragon_ring", 5),
        ("skill_cache_10", 5),
        ("skill_cache_20", 3),
        ("skill_cache_30", 1),
    ],
    "interesting_gear": [
        ("crusty_sword", 15),
        ("froghide_armor", 14),
        ("obsidian_amulet", 10),
        ("moonbite_dagger", 9),
        ("echo_plate", 9),
        ("warding_totem", 8),
        ("dragon_ring", 4),
        ("dragon_shield", 3),
    ],
}
