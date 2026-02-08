"""Item definitions for byte_world_ai."""

from __future__ import annotations

from typing import Dict


ITEMS: Dict[str, dict] = {
    "rusted_blade": {
        "name": "Rusted Blade",
        "type": "weapon",
        "description": "A chipped sword that still holds an edge.",
        "attack_bonus": 1,
        "value": 8,
    },
    "patched_coat": {
        "name": "Patched Coat",
        "type": "armor",
        "description": "Threadbare but serviceable cloth armor.",
        "defense_bonus": 1,
        "max_hp_bonus": 2,
        "value": 8,
    },
    "minor_potion": {
        "name": "Minor Potion",
        "type": "consumable",
        "description": "Restores a small amount of health.",
        "heal_amount": 18,
        "value": 10,
    },
    "sturdy_bandage": {
        "name": "Sturdy Bandage",
        "type": "consumable",
        "description": "A field dressing used between skirmishes.",
        "heal_amount": 12,
        "value": 6,
    },
    "crusty_sword": {
        "name": "Crusty Sword",
        "type": "weapon",
        "description": "Rust and swamp slime hide surprising sharpness.",
        "attack_bonus": 4,
        "value": 35,
    },
    "froghide_armor": {
        "name": "Froghide Armor",
        "type": "armor",
        "description": "Thick hide that shrugs off glancing blows.",
        "defense_bonus": 3,
        "max_hp_bonus": 6,
        "value": 32,
    },
    "crusty_key": {
        "name": "Crusty Key",
        "type": "key",
        "description": "An old key caked in swamp grit.",
        "value": 0,
    },
    "obsidian_scimitar": {
        "name": "Obsidian Scimitar",
        "type": "weapon",
        "description": "A curved black blade forged for fast strikes.",
        "attack_bonus": 7,
        "value": 80,
    },
    "dragon_armor": {
        "name": "Dragon Armor",
        "type": "armor",
        "description": "Scaled plate that channels heat into protection.",
        "defense_bonus": 6,
        "max_hp_bonus": 12,
        "value": 85,
    },
    "obsidian_amulet": {
        "name": "Obsidian Amulet",
        "type": "accessory",
        "description": "A volcanic charm that hardens your resolve.",
        "attack_bonus": 2,
        "defense_bonus": 1,
        "value": 55,
    },
    "mysterious_ring": {
        "name": "Mysterious Ring",
        "type": "accessory",
        "description": "Warm to the touch. It hums when danger peaks.",
        "attack_bonus": 1,
        "defense_bonus": 1,
        "value": 60,
    },
    "dragon_ring": {
        "name": "Dragon Ring",
        "type": "accessory",
        "description": "A ring carved from horn and fused with ash.",
        "attack_bonus": 3,
        "value": 95,
    },
    "dragon_shield": {
        "name": "Dragon Shield",
        "type": "shield",
        "description": "A heavy shield from the ogre's stolen hoard.",
        "defense_bonus": 5,
        "max_hp_bonus": 8,
        "value": 90,
    },
    "hoard_treasure": {
        "name": "Hoard of Treasure",
        "type": "quest",
        "description": "An overstuffed sack of coins and relics.",
        "value": 200,
    },
    "goblin_riddle": {
        "name": "Goblin Riddle",
        "type": "quest",
        "description": "A scribbled riddle rumored to break black magic.",
        "value": 0,
    },
    "makor_soul": {
        "name": "Makor's Soul",
        "type": "aura",
        "description": "A volatile aura: savage offense, brittle defense.",
        "attack_bonus": 9,
        "defense_bonus": -4,
        "value": 0,
    },
    "vial_of_tears": {
        "name": "Vial of Tears",
        "type": "quest",
        "description": "Silvery tears able to strip corruption from Elle.",
        "value": 0,
    },
    "moonbite_dagger": {
        "name": "Moonbite Dagger",
        "type": "weapon",
        "description": "A rare dagger that punishes overconfident foes.",
        "attack_bonus": 5,
        "value": 50,
    },
    "echo_plate": {
        "name": "Echo Plate",
        "type": "armor",
        "description": "A rare chestplate that dampens impact.",
        "defense_bonus": 4,
        "max_hp_bonus": 10,
        "value": 60,
    },
    "warding_totem": {
        "name": "Warding Totem",
        "type": "aura",
        "description": "A rare aura that thickens your guard.",
        "defense_bonus": 4,
        "value": 75,
    },
    "skill_cache_10": {
        "name": "Skill Cache (+10)",
        "type": "boon",
        "description": "Instantly grants 10 skill points.",
        "skill_points_bonus": 10,
        "value": 0,
    },
    "skill_cache_20": {
        "name": "Skill Cache (+20)",
        "type": "boon",
        "description": "Instantly grants 20 skill points.",
        "skill_points_bonus": 20,
        "value": 0,
    },
    "skill_cache_30": {
        "name": "Skill Cache (+30)",
        "type": "boon",
        "description": "Instantly grants 30 skill points.",
        "skill_points_bonus": 30,
        "value": 0,
    },
}


EQUIPMENT_SLOT_BY_TYPE = {
    "weapon": "weapon",
    "armor": "armor",
    "shield": "shield",
    "accessory": "accessory",
    "aura": "aura",
}

