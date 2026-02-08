# byte_world_ai — High-Level Design Spec

## Abstract
A CLI-based RPG/explorer game. Think **"Runescape"**, but much more simplified: only a few skills, a few NPC encounters, a few bosses, and a few loot types. There are no graphics (except rare ASCII moments in the CLI). This is a mini learning project to practice Python.

---

## High-level Design

### Character
- One main character that the player pilots
- Piloted with commands in the CLI
- All movement is turn-based (the player selects where to go next; no traditional movement)
- Progresses the main storyline quest and obtains titles/loot by exploring, meeting NPCs, defeating bosses, and leveling skills

### NPCs
- Starts with **2 NPCs**
- **Wise Old Man (early game)**
  - Introduces the story and quest
  - Provides options on where to go next
  - Gives subtle hints in dialogue (no obvious “choose A/B” prompts; player discovers the path decision tree)
- **Elle (late game / long-lost daughter)**
  - Held captive by the final boss
  - You learn she is still alive from the Wise Old Man, but you don’t expect to find her here until after defeating the boss

---

## Bosses

### Giant Frog
- **Description:** Encountered in a swamp (one of the first sub-areas after meeting the Wise Old Man)
- **Location:** Forest of Magic / Swamp
- **Loot:** Crusty key, crusty sword, froghide armor, skill points (attack/defense/HP)
- **Dialogue:**
  - **Pre-fight:** Frog introduces himself as the Prince of the Swamp; you learn he holds a dark secret inside him
  - **Post-fight:** You find a crusty key on his corpse. The game reveals the Onyx Witch dumped it in this far-away swamp to hide something, and the frog ate it

### Dragon
- **Description:** Encounter at the peak of a mountain
- **Location:** Dragon Mountain / Peak
- **Loot:** Mysterious ring, dragon armor, obsidian amulet, obsidian scimitar, skill points (attack/defense/HP)
- **Dialogue:**
  - **Pre-fight:** Hissing threats; warns you nobody survives the peak, “not even Makor’s oldest son.” Lands atop the crumbled bones of Makor II’s corpse
  - **Post-fight:** Turns to dust; an echo in the wind hints at treasure nearby, but warns of dangerous perils if sought

### Ogre (Optional)
- **Description:** Encountered in a cave (optional area). Only available after you kill the dragon. The dragon mentions treasure in a nearby cave with its dying breath; you can choose to go or skip it.
- **Location:** Dragon Mountain / Cave
- **Loot:** Hoard of treasure, dragon ring, dragon shield, skill points (attack/defense/HP)
- **Dialogue:**
  - **Pre-fight:** Ogre screams at you to leave or die, claiming the cave is his
  - **Post-fight:** Before dying, he tells you to take the hoard back to the Wise Old Man when you see him next

### Army of Goblins
- **Description:** Encountered on the desolate road (in the 2nd set of areas). You can bribe your way out by:
  - telling them a joke, or
  - handing over treasure,
  - or fight them instead.
- **Location:** Makor’s Castle / Desolate Road
- **Loot:** Riddle (used later to defeat the witch; antidote to her curse), skill points (attack/defense/HP)
- **Dialogue:**
  - **Pre-fight:** They sneak up, tie you up, and taunt you for traveling near Makor’s Castle.
    - If you tell a joke: they laugh and let you go
    - If you offer gold: you try to give half; they take all, then let you go
    - If you fight: they scream with laughter and taunt you
    - If you fight and lose: 50% chance they reduce one of your skill points by -1
  - **Post-fight:** If you fight, you kill them all except one who bargains for his life by handing you a riddle

### King Makor the Rot (Penultimate Boss)
- **Description:** The corrupted king. Once good, he met a witch who corrupted him and stole his heart.
- **Location:** Makor’s Castle / Royal Hall AND Makor’s Castle / Dungeon
- **Loot:** Makor’s Soul (aura: much stronger offense, weaker defense), skill points (attack/defense/HP)
- **Dialogue:**
  - **Pre-fight:** In the Black Hall, a loud echoing voice welcomes you. He says he’s heard about you from Elle (first hint of where she is). Two bright red eyes appear; a tall, dark-armored pale man appears, smiles… your eyes go black.
    - You wake in a dungeon; he toys with you and thinks you’re weak.
    - You remember the ring’s “rub when in time of need.” You rub it, surge with power, and begin fighting him.
  - **Post-fight:** On your final thrust he begs forgiveness. You smile and strike again. He screams “you’ll never defeat her” and turns to dust.

### Onyx Witch (Final Boss)
- **Description:** You learn all prior creatures were her minions (except the goblins—odd). Her black magic makes her “impossible” to fight; she binds you with a spell that renders you useless and slowly kills you.
- **Location:** Makor’s Castle / Witch’s Terrace
- **Loot:** Elle; vial of tears (used to remove corruption from Elle)
- **Dialogue:**
  - **Pre-fight:** She shows you Elle, mocks Makor’s weakness, and boasts you can never kill her. She binds you with black magic so you can’t attack.
  - **Mid-fight:** You discover and read the riddle in your bag; it breaks the black magic and you can fight.
  - **Post-fight:** Her soul collapses inward; her spirit rushes into the floor; an echo screams like a thousand demons, then silence. You free Elle using the crusty key.

---

## Locations

### 1) Forest of Magic
**Sub-areas:**
- **Old Shack (intro / Wise Old Man)**
  - Skills learned: attack, defense, health
  - Small creatures: rats
  - Skill points per small-creature kill: +1
  - Notes: very small chance for small creatures to drop rare armor/weapons, rare auras, or big skill upgrades (+10/+20/+30). Player can train here before continuing.
- **Forest**
  - Small creatures: wolves
  - Skill points per kill: +2
- **Swamp (Giant Frog boss)**
  - Small creatures: none
  - Skill points per kill: N/A
- **Underground Tunnel**
  - Small creatures: giant mole
  - Skill points per kill: +3

### 2) Dragon Mountain
**Sub-areas:**
- **Base**
  - Small creatures: whelps
  - Skill points per kill: +4
- **Abandoned Mine**
  - Small creatures: corrupt dwarves
  - Skill points per kill: +5
- **Peak (Dragon boss)**
  - Small creatures: none
  - Skill points per kill: N/A
- **Cave (optional / Ogre boss)**
  - Small creatures: none
  - Skill points per kill: N/A

### 3) Makor’s Castle
**Sub-areas:**
- **Desolate Road (Goblins boss)**
  - Small creatures: goblin squires
  - Skill points per kill: +6
- **Royal Yard**
  - Small creatures: corrupted knights
  - Skill points per kill: +7
- **Black Hall (meet Makor)**
  - Small creatures: none
  - Skill points per kill: N/A
- **Dungeon (fight Makor)**
  - Small creatures: none
  - Skill points per kill: N/A
- **Witch’s Terrace (Onyx Witch boss)**
  - Small creatures: none
  - Skill points per kill: N/A

---

## Gameplay

- **Between boss fights:**
  - Player chooses whether to grind small creatures to level skills or proceed to the next location
  - Exceptions:
    - Old Shack acts as intro/tutorial + optional grinding
    - Bo
