                                                ### FILE STRUCTURE ###
byte_world_ai/
  main.py
  spec.md

  game/
    engine.py        # main loop + command routing
    commands.py      # text -> (command, args)
    state.py         # GameState container (single source of truth)
    ui.py            # printing helpers (optional but nice)

  systems/
    exploration.py   # move/look/sense + encounters
    combat.py        # turn-based combat loop
    loot.py          # drops + equip rules
    quest.py         # quest stages + trigger checks

  content/
    world.py         # location graph + encounter tables (dicts)
    enemies.py       # enemy/boss stat definitions (dicts)
    items.py         # item definitions + modifiers (dicts)
    quests.py        # quest stages + requirements (dicts)

-----------------------------------------------------------------------

### ARCHITECTURE ###

# byte_world_ai — MVP High-Level Architecture (LLD Template)

## Scope (MVP Only: Area 1)
**Playable Area 1**
- Old Shack (Wise Old Man)
- Forest
- Swamp (Boss: Giant Frog)
- Underground Tunnel

**Enemies**
- 2–3 normal enemies (e.g., rat/wolf/mole)
- 1 boss: Giant Frog

**Loot**
- Gold
- 1 potion
- 1 weapon
- 1 armor
- Boss drop: **crusty key** (quest item)

**Skills**
- 1 skill unlocked early (Wise Old Man)

**Quest**
- Meet wise old man → reach swamp → defeat frog → obtain crusty key → “Chapter complete”


---

## 1) Project File Structure (MVP)


**MVP principle:** Use Python dicts in `content/` first. JSON can be an expansion.

---

## 2) Architecture Rule: One Truth, Many Systems

### Single Source of Truth
All mutable game data lives in **GameState**:
- player
- current location
- quest stage
- flags
- active encounter

### Systems
Each system function:
- reads `state`
- updates `state` as needed
- returns **messages/results** for UI

### Flow (High Level)
1. `engine` prints prompt and reads input
2. `commands` parses input -> `command_name, args`
3. `engine` dispatches to the correct handler
4. handler calls one or more `systems/*`
5. `ui` prints output

---

## 3) Core Data Model (Minimum)

### GameState
- `player`
- `current_location_id`
- `quest_stage` (int or string key)
- `flags` (dict/set for milestones like `met_old_man`, `frog_defeated`)
- `active_encounter` (None or enemy data object)

### Player
- Base stats: `max_hp`, `attack`, `defense`
- Current: `hp`, `xp`, `level`, `skill_points`, `gold`
- `inventory` (item_id -> quantity)
- `equipment` (weapon_id, armor_id)
- `skills` (skill_id list + per-skill cooldown/uses state)

**Design guideline:** Keep base stats separate from equipment bonuses; compute “effective stats” when needed.

---

## 4) Content Data Shapes (Dict-Based)

### `content/world.py`
`LOCATIONS = { location_id: location_data }`

Each `location_data` includes:
- `name`
- `descriptions` (list[str]) for variety
- `exits` (dict: direction -> location_id)
- `encounters` (list or weighted table of enemy_ids)
- optional: `is_safe` (bool) for Old Shack

### `content/enemies.py`
`ENEMIES = { enemy_id: enemy_data }`

Each `enemy_data` includes:
- `name`
- `hp`, `attack`, `defense`
- `xp_reward`, `gold_reward`
- `loot_table` (weighted list of item_ids)

Boss-only fields (MVP):
- `intents` (2+ moves with telegraph text + effect)
- simple behavior rule (alternate moves OR conditional)

### `content/items.py`
`ITEMS = { item_id: item_data }`

Each `item_data` includes:
- `name`
- `type` in {`weapon`, `armor`, `consumable`, `key`}
- `description`
- modifiers/effects:
  - weapon: `attack_bonus`
  - armor: `defense_bonus` or `max_hp_bonus`
  - consumable: `heal_amount`
  - key: no stats

### `content/quests.py`
`QUEST_STAGES = [ stage0, stage1, ... ]` OR dict keyed by stage id

Each stage includes:
- `description` (what `quest` prints)
- `completion_condition` (checked via flags/state)
- `on_complete` effects (set flag, give item, etc.)

---

## 5) Commands (MVP)

### Required commands
- `help`
- `status`
- `look`
- `sense`
- `move <north|south|east|west>` (aliases: `n/s/e/w`)
- `inventory`
- `equip <item>`
- `use <item>`
- `fight`
- `run`
- `quest`
- `quit`

### Command rules
- If `active_encounter` exists:
  - block `move`
  - allow combat commands (`fight`, `run`, `use`, `status`)

---

## 6) Module Responsibilities (High Level)

### `main.py`
- bootstraps content (imports `content/*`)
- creates initial `GameState`
- starts `Engine.run(state)`

### `game/commands.py`
- parse raw input string -> `(command_name, args)`
- normalization (trim, lowercase)
- alias mapping (`n` -> `move north`)

### `game/engine.py`
- main loop
- dispatch table: `{command_name: handler_fn}`
- each handler:
  - validates rules (e.g., cannot move during encounter)
  - calls systems
  - returns messages for UI

### `game/ui.py`
- formatting helpers for:
  - location screen (name + description)
  - status output
  - inventory output
  - combat messages

### `systems/exploration.py`
Responsibilities:
- `look(state)` -> description
- `sense(state)` -> hint text
- `move(state, direction)` -> update location
- on entry: roll encounter chance and set `state.active_encounter`

### `systems/combat.py`
Responsibilities:
- `start_or_resolve_combat(state, player_action)` (or similar)
- damage calculation + turn order
- boss telegraphing:
  - show intent text before enemy action
  - resolve based on player choice (attack/defend/etc.)
- handle win/lose outcomes:
  - win -> grant rewards via `loot` + quest checks
  - lose -> respawn behavior (MVP: reset location to Old Shack, partial HP)

### `systems/loot.py`
Responsibilities:
- `grant_rewards(state, enemy_id)` -> XP, gold, item drops
- `equip_item(state, item_id)` -> update equipment
- `use_item(state, item_id)` -> apply potion effect, reduce qty

### `systems/quest.py`
Responsibilities:
- `get_current_objective(state)` -> string
- `check_and_advance(state)` -> progress quest based on flags/state

---

## 7) Combat Design (MVP Boss Strategy)

### Player actions (MVP)
- `attack`
- `defend` (reduce next incoming damage)
- `use <potion>`
- `skill <name>` (optional if unlocked)
- `run` (chance-based; boss may reduce success chance)

### Boss telegraph pattern (text-based strategy)
- Enemy reveals **intent**: “The frog inflates and its throat glows…”
- Player chooses response: attack / defend / use / skill
- Resolve enemy action with response modifiers

**Requirement:** Boss has at least 2 distinct intents with different best responses.

---

## 8) Build Milestones (Assignment Checkpoints)

### Milestone 1 — Engine + Parsing
Deliver:
- loop runs
- `help`, `quit`, `status`, `look`
Pass:
- no crashes on unknown commands

### Milestone 2 — World + Movement
Deliver:
- 4 locations connected
- `move` updates location
- `sense` provides a hint
Pass:
- walk Old Shack → Forest → Swamp → Tunnel

### Milestone 3 — Encounters + Basic Combat
Deliver:
- encounter can spawn (Forest/Tunnel)
- `fight` resolves combat loop
- `run` sometimes escapes
Pass:
- win 2 fights, gain XP

### Milestone 4 — Loot + Equipment
Deliver:
- `inventory`, `equip`, `use potion`
- equipping changes stats shown in `status`
Pass:
- gear impacts combat outcome

### Milestone 5 — Boss + Quest Completion
Deliver:
- Giant Frog fight with telegraphs
- boss drops crusty key
- quest advances to “Chapter complete”
Pass:
- complete MVP from fresh start

---

## 9) MVP Definition of Done
- Complete Area 1 storyline in one session
- No hard crashes on invalid input
- Stats + gear impact combat meaningfully
- Boss uses telegraphed intents with meaningful player responses


