# byte_world_ai

`byte_world_ai` is a text-first, command-driven fantasy RPG with tactical turn-based combat, guided progression, and terminal-friendly readability features.

You can play it:
- in a local Python terminal (CLI mode), or
- in a browser on GitHub Pages (web terminal mode).

## Play Online

Live site: `https://jordanbailey00.github.io/byte_world_ai/`

## Table of Contents

- [What Kind of Game Is This?](#what-kind-of-game-is-this)
- [Quick Start](#quick-start)
- [Core Loop](#core-loop)
- [Command Reference](#command-reference)
- [UI and Readability Features](#ui-and-readability-features)
- [Combat System](#combat-system)
- [Progression and Stats](#progression-and-stats)
- [Items, Gear, and Training](#items-gear-and-training)
- [World and Area Guide](#world-and-area-guide)
- [Quest Route and Boss Guide](#quest-route-and-boss-guide)
- [Tips for New Players](#tips-for-new-players)
- [FAQ](#faq)
- [Technical and Deployment Notes](#technical-and-deployment-notes)

## What Kind of Game Is This?

`byte_world_ai` is designed around readable terminal gameplay:
- every prompt shows all currently valid actions,
- combat prompts only show combat-relevant actions,
- interactable entities are color-coded,
- maps and quest hints are always accessible by command.

Main goals:
- defeat the major story bosses,
- rescue and cleanse Elle,
- complete the main questline,
- optionally continue exploring and farming afterward.

## Quick Start

### Option 1: Play in browser (recommended)

Open:

`https://joey1399.github.io/byte_world_ai/`

Notes:
- this version is static-hosted on GitHub Pages,
- Python runs in-browser via Pyodide,
- page refresh starts a fresh run (no persistent save yet).

### Option 2: Play local CLI

Requirements:
- Python 3.10+ (3.12+ recommended)

Run:

```bash
python main.py
```

### Option 3: Preview the web build locally

```bash
python -m http.server 8000
```

Then open:

`http://localhost:8000`

## Core Loop

1. Read the action hints shown at the prompt.
2. Enter one command.
3. Review the result block.
4. Repeat until quest progression, victory, or quit.

General flow:
- talk to the Wise Old Man,
- clear swamp -> mountain -> castle route,
- handle goblin road encounter,
- defeat Makor, then the Onyx Witch,
- free and cleanse Elle.

## Command Reference

All commands are case-insensitive. Partial item/NPC matching is supported when practical.

### Movement and navigation

| Command | Description |
|---|---|
| `move north` / `move south` / `move east` / `move west` / `move up` / `move down` | Travel if exit is unlocked and no active encounter. |
| `map` | Shows a directional ASCII map from current location with lock/recommendation labels. |
| `look` | Re-describes location, exits, and visible NPCs. |
| `sense` | Gives contextual environmental hints. |

### Information

| Command | Description |
|---|---|
| `status` | Shows level, HP, effective stats, XP, skill points, gold, titles, and equipped gear. |
| `quest` | Shows current quest stage, description, and hint. |
| `inventory` | Lists all owned items and types. |
| `help` | Full in-game command menu. |
| `quit` | Ends current session. |

### Social

| Command | Description |
|---|---|
| `talk wise old man` | Starts progression and grants core skills the first time. |
| `talk elle` | Available at Witch's Terrace after relevant story events. |

### Gear and item use

| Command | Description |
|---|---|
| `equip <item>` | Equip one item by name/query. |
| `equip all` | Auto-equip best-in-slot across weapon/armor/shield/accessory/aura. |
| `use <item>` | Use consumables or context-sensitive quest/key items. |
| `read <item>` | Reads special items such as Goblin Riddle. |

### Progression

| Command | Description |
|---|---|
| `train attack <n>` | Spend skill points for base ATK. |
| `train defense <n>` | Spend skill points for base DEF. |
| `train health <n>` | Spend skill points for base max HP (`+3` max HP per point). |
| `train all` | Splits available points equally among attack/defense/health. |
| `train a,b,c` | Exact allocation: `attack,defense,health` (example: `train 3,4,3`). |

### Combat

| Command | Description |
|---|---|
| `fight` | Basic attack. |
| `defend` | Reduces next incoming enemy hit based on intent multipliers. |
| `skill focus strike` | Heavy hit (~1.8x attack), 2-turn cooldown. |
| `skill guard stance` | Defend + heal 6 HP, 3-turn cooldown. |
| `skill second wind` | Heal 16 HP, 4-turn cooldown. |
| `run` | Escape attempt (chance depends on enemy category). |
| `joke` | Goblin Army negotiation-only option. |
| `bribe` | Goblin Army negotiation-only option (cost: all current gold). |

### Command aliases

| Alias | Expands to |
|---|---|
| `n s e w u d` | `move north/south/east/west/up/down` |
| `north south east west up down` | `move <dir>` |
| `m` | `map` |
| `i`, `inv` | `inventory` |
| `q`, `exit` | `quit` |
| `attack`, `atk` | `fight` |

## UI and Readability Features

### Dynamic action hints

At every input prompt, the game prints all valid actions with short descriptions based on your exact state.

Behavior:
- out of combat: all relevant world/inventory/progression actions,
- in combat: only combat-relevant actions for the active encounter.

### Color legend

| Color | Meaning |
|---|---|
| Blue | Talkable NPC |
| Yellow | Fightable creature |
| Orange | Boss |
| Red | End-boss (King Makor, Onyx Witch) |
| Green | Item/equipment |
| Purple | Rare/quest/important reward item |
| Pink | Skill/stat terms (`attack`, `defense`, `health`, skill names) |

### Combat health bars

During combat, ASCII health bars are shown after attacks:
- green segment = current HP,
- red segment = missing HP.

Both player and enemy bars are displayed.

### Terminal clearing

The CLI clears the previous screen output each turn (to reduce clutter).

Env toggles:
- `BYTE_WORLD_AI_NO_CLEAR=1` disables clear behavior,
- `BYTE_WORLD_AI_FORCE_CLEAR=1` forces clear behavior when terminal checks fail.

## Combat System

### Turn structure

1. Player chooses an action.
2. If action consumes a turn and enemy survives, enemy acts.
3. Cooldowns tick after enemy turn.

### Key rules

- `defend` applies to next enemy hit only.
- some actions do not consume a turn (context-dependent item uses).
- movement/talking/training are blocked while encounter is active.

### Escape chances

- Normal enemies: ~65%
- Bosses: ~28%
- Goblin Army: ~22%

Failed escape triggers enemy turn.

### Encounter-specific mechanics

- **Goblin Army**: starts in negotiation phase with `joke`, `bribe`, or `fight`.
- **Onyx Witch**: starts with barrier active; normal attacks are blocked until Goblin Riddle is read/used.
- **Onyx Witch curse**: while barrier is active, enemy turns apply extra 4 HP drain.
- **King Makor**: if `Mysterious Ring` is in inventory, ring surge auto-activates at encounter start (`+4 ATK`, `+2 DEF` temporary bonus).

### Defeat behavior

On defeat:
- encounter ends,
- you respawn at `Old Shack`,
- HP is restored to 50% of effective max HP.

Extra penalty:
- versus Goblin Army, there is a 50% chance of permanent `-1` to one base stat (attack/defense/health).

## Progression and Stats

### Starting character

- Name: `Wanderer`
- Base max HP: `50`
- Base attack: `8`
- Base defense: `5`
- Starting gold: `20`
- Starting inventory: Rusted Blade, Patched Coat, Minor Potion x2, Sturdy Bandage x1

### Effective stats

Effective combat stats are:
- base stats
- plus equipped gear bonuses
- plus temporary bonuses (for example ring surge)

### Leveling

XP required to next level:

`40 + (level - 1) * 30`

On level up:
- `+6` base max HP
- `+1` base attack
- `+1` base defense
- full heal to effective max HP

### Skill points

Skill points come from:
- boss rewards,
- normal enemy area bonuses (`skill_points_per_kill`),
- rare boon drops (`Skill Cache` items).

## Items, Gear, and Training

### Equipment slots

- `weapon`
- `armor`
- `shield`
- `accessory`
- `aura`

### Best-in-slot auto-equip

`equip all` compares all owned equippable items and equips the strongest option per slot.

Scoring basis:
- attack bonus,
- defense bonus,
- max HP bonus (normalized),
- item value as tie-break support.

### Consumables

| Item | Effect |
|---|---|
| `Minor Potion` | Heal 18 HP |
| `Sturdy Bandage` | Heal 12 HP |

### Important quest/context items

| Item | Core purpose |
|---|---|
| `Crusty Key` | Frees Elle at Witch's Terrace after Witch defeat |
| `Goblin Riddle` | Breaks Onyx Witch barrier |
| `Vial of Tears` | Cleanses Elle and completes story |
| `Hoard of Treasure` | Turn in at Old Shack for 180 gold via `use hoard` |
| `Mysterious Ring` | Temporary combat surge (`+4 ATK`, `+2 DEF`) |

### Loot drop rules

| Rule | Value |
|---|---|
| Guaranteed boss drops | Always drop |
| Extra loot-table roll (normal enemies) | 45% |
| Extra loot-table roll (bosses) | 70% |
| Rare boon roll (normal enemies) | 4% |
| Rare boon pool | `Moonbite Dagger`, `Echo Plate`, `Warding Totem`, `Skill Cache (+10/+20/+30)` |

### Training conversions

- `train attack 1` -> `+1` base ATK
- `train defense 1` -> `+1` base DEF
- `train health 1` -> `+3` base max HP

`train all` behavior:
- spends points in equal split,
- leftover points remain unspent.

## World and Area Guide

This map is mostly linear with optional side farming and one optional boss cave.

### Location stats

| Location | Encounter chance | Creature variants | Skill points per normal kill | Notes |
|---|---:|---:|---:|---|
| Old Shack | 0.28 | 20 | 1 | Start area, Wise Old Man |
| Forest | 0.48 | 20 | 2 | Gate to swamp/mountain |
| Swamp | 0.00 | 0 | 0 | Giant Frog boss zone |
| Underground Tunnel | 0.52 | 20 | 3 | Farm branch off Forest |
| Dragon Mountain Base | 0.56 | 20 | 4 | Hub to peak/mine/road |
| Abandoned Mine | 0.62 | 20 | 5 | High-yield farm branch |
| Dragon Mountain Peak | 0.00 | 0 | 0 | Ash Dragon boss zone |
| Dragon Mountain Cave | 0.00 | 0 | 0 | Optional Hoard Ogre boss |
| Desolate Road | 0.52 | 20 | 6 | Goblin Army event route |
| Royal Yard | 0.60 | 20 | 7 | Last farm zone before castle interior |
| Black Hall | 0.00 | 0 | 0 | Cutscene transition to Dungeon |
| Dungeon | 0.00 | 0 | 0 | King Makor boss zone |
| Witch's Terrace | 0.00 | 0 | 0 | Onyx Witch + Elle |

Each farmable non-boss location has 20 creature variants (1 base + 19 generated variants).

### Route locks

- Forest -> Mountain Base (`north`) requires `frog_defeated`.
- Mountain Base -> Desolate Road (`west`) requires `dragon_defeated`.
- Mountain Peak -> Mountain Cave (`east`) requires `dragon_defeated`.
- Royal Yard -> Black Hall (`north`) requires Goblin route resolved (`goblin_army_defeated` or `goblin_pass_granted`).
- Black Hall -> Witch's Terrace (`north`) requires `makor_defeated`.

## Quest Route and Boss Guide

### Main quest stages

1. Awakening
2. The Swamp Secret
3. Ash on the Peak
4. Road of Knives
5. King in Rot
6. Break the Curse
7. Rescue Elle
8. Homecoming

### Boss summary

| Boss | HP | Special mechanic | Guaranteed drops |
|---|---:|---|---|
| Giant Frog, Prince of the Swamp | 85 | Standard boss intents | Crusty Key, Crusty Sword, Froghide Armor |
| Ash Dragon | 130 | Standard boss intents | Mysterious Ring, Dragon Armor, Obsidian Amulet, Obsidian Scimitar |
| Hoard Ogre (optional) | 150 | Optional cave boss | Hoard of Treasure, Dragon Ring, Dragon Shield |
| Army of Goblins | 165 | Negotiation phase (`joke`, `bribe`, `fight`) | Goblin Riddle |
| King Makor the Rot | 190 | Ring surge synergy if ring owned | Makor's Soul |
| The Onyx Witch | 230 | Barrier blocks attacks until riddle; curse drain while active | Vial of Tears |

### Titles from boss kills

- Giant Frog -> `Swampbreaker`
- Ash Dragon -> `Peakslayer`
- Hoard Ogre -> `Hoardbreaker`
- Army of Goblins -> `Road Reaper`
- King Makor -> `Rotbane`
- Onyx Witch -> `Witchfall Champion`

### Story completion condition

Main storyline completes when:
- Onyx Witch is defeated,
- Elle is freed,
- `Vial of Tears` is used at Witch's Terrace to cleanse Elle.

After completion, you can keep playing or `quit`.

## Tips for New Players

- Talk to the Wise Old Man immediately to unlock your core skill set.
- Farm Forest/Tunnel if first bosses feel too strong.
- Use `map` frequently to follow recommended route markers.
- Use `equip all` after major loot drops.
- Save healing items for bosses or failed escape outcomes.
- Against Onyx Witch, prioritize breaking barrier with `read goblin riddle` or `use goblin riddle`.
- If Goblin Army negotiation starts early, `joke` or `bribe` can bypass direct combat.

## FAQ

### Why can’t I move/talk/train right now?

You are likely in an active encounter. Resolve it with combat actions or `run`.

### Why am I not damaging the Onyx Witch?

Her barrier is active. Use/read Goblin Riddle in combat to break it first.

### Why did I wake up in Old Shack?

You were defeated in combat. Defeat causes respawn at Old Shack with partial HP.

### Can I continue after winning?

Yes. Main quest victory does not force quit.

### Is there save/load?

Not yet. Runs are session-based.

## Technical and Deployment Notes

### GitHub Pages

This repository deploys via:

`.github/workflows/pages.yml`

Pages is configured with GitHub Actions as the build source.

### Local static web runtime details

- `index.html` + `static/app.js` host a terminal-like UI.
- The Python game engine is loaded in-browser via Pyodide CDN.
- No backend server is required for the web build.

### Optional environment toggles (CLI)

- `BYTE_WORLD_AI_NO_CLEAR=1`
- `BYTE_WORLD_AI_FORCE_CLEAR=1`
- `BYTE_WORLD_AI_FORCE_COLOR=1`
- `NO_COLOR=1` (disables color)
