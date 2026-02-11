(() => {
  const terminal = document.getElementById("terminal");
  const form = document.getElementById("command-form");
  const input = document.getElementById("command-input");
  const sendButton = document.getElementById("send-button");
  const resetButton = document.getElementById("reset-button");
  const statusLine = document.getElementById("status-line");
  const statusPanel = document.getElementById("status-panel");
  const statusEmpty = document.getElementById("status-empty");
  const artTitle = document.getElementById("art-title");
  const artPanel = document.getElementById("art-panel");
  const artImage = document.getElementById("art-image");
  const actionsTitle = document.getElementById("actions-title");
  const actionsList = document.getElementById("actions-list");
  const actionsEmpty = document.getElementById("actions-empty");
  const hintsToggle = document.getElementById("hints-toggle");

  const PYODIDE_JS_URL = "https://cdn.jsdelivr.net/pyodide/v0.29.3/full/pyodide.js";
  const SOURCE_FILES = [
    "content/__init__.py",
    "content/enemies.py",
    "content/items.py",
    "content/quests.py",
    "content/world.py",
    "content/art/ascii-art.txt",
    "game/__init__.py",
    "game/commands.py",
    "game/engine.py",
    "game/state.py",
    "game/ui.py",
    "systems/__init__.py",
    "systems/combat.py",
    "systems/exploration.py",
    "systems/loot.py",
    "systems/quest.py",
  ];
  const ANSI_CLASS_BY_CODE = {
    "38;5;39": "ansi-blue",
    "93": "ansi-yellow",
    "38;5;208": "ansi-orange",
    "91": "ansi-red",
    "92": "ansi-green",
    "95": "ansi-purple",
    "38;5;213": "ansi-pink",
  };
  const ANSI_PATTERN = /\x1b\[([0-9;]+)m/g;
  const CONTROL_PATTERN = /\x1b\[(?![0-9;]*m)[0-9;]*[A-Za-z]/g;
  const ACTION_BUCKET_ORDER = ["movement", "combat", "quest", "player"];
  const ACTION_BUCKET_LABEL = {
    movement: "Movement",
    combat: "Combat",
    quest: "Quest",
    player: "Player",
  };
  const HINT_STORAGE_KEY = "byte_world_ai_hints_enabled";
  const SAVE_STORAGE_KEY = "byte_world_ai_save_v1";

  let pyodide = null;
  let api = null;
  let busy = false;
  let gameOver = false;
  let initialized = false;
  let hintsEnabled = true;
  let lastPayload = null;

  function escapeHtml(text) {
    return text
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#39;");
  }

  function ansiToHtml(text) {
    const raw = String(text || "");
    const clean = raw.replace(CONTROL_PATTERN, "").replaceAll("\r", "");
    let rendered = "";
    let index = 0;
    let openSpan = false;
    ANSI_PATTERN.lastIndex = 0;

    while (true) {
      const match = ANSI_PATTERN.exec(clean);
      if (!match) {
        break;
      }

      rendered += escapeHtml(clean.slice(index, match.index));
      const code = match[1];
      if (code === "0") {
        if (openSpan) {
          rendered += "</span>";
          openSpan = false;
        }
      } else {
        const cssClass = ANSI_CLASS_BY_CODE[code];
        if (cssClass) {
          if (openSpan) {
            rendered += "</span>";
          }
          rendered += `<span class="${cssClass}">`;
          openSpan = true;
        }
      }

      index = match.index + match[0].length;
    }

    rendered += escapeHtml(clean.slice(index));
    if (openSpan) {
      rendered += "</span>";
    }
    return rendered;
  }

  function setStatus(message, isError = false) {
    statusLine.textContent = message;
    statusLine.classList.toggle("over", Boolean(isError));
  }

  function readSavedGame() {
    try {
      return window.localStorage.getItem(SAVE_STORAGE_KEY);
    } catch (_error) {
      return null;
    }
  }

  function writeSavedGame(snapshot) {
    try {
      window.localStorage.setItem(SAVE_STORAGE_KEY, snapshot);
    } catch (_error) {
      // Ignore storage write failures.
    }
  }

  function clearSavedGame() {
    try {
      window.localStorage.removeItem(SAVE_STORAGE_KEY);
      const staleKeys = [];
      for (let index = 0; index < window.localStorage.length; index += 1) {
        const key = window.localStorage.key(index);
        if (key && key.startsWith("byte_world_ai_save_")) {
          staleKeys.push(key);
        }
      }
      for (const key of staleKeys) {
        window.localStorage.removeItem(key);
      }
    } catch (_error) {
      // Ignore storage failures.
    }
  }

  function loadHintsPreference() {
    try {
      const stored = window.localStorage.getItem(HINT_STORAGE_KEY);
      if (stored === "0") {
        hintsEnabled = false;
      } else if (stored === "1") {
        hintsEnabled = true;
      }
    } catch (_error) {
      hintsEnabled = true;
    }
  }

  function saveHintsPreference() {
    try {
      window.localStorage.setItem(HINT_STORAGE_KEY, hintsEnabled ? "1" : "0");
    } catch (_error) {
      // Ignore storage failures (privacy mode, blocked storage, etc.).
    }
  }

  function updateHintsToggleLabel() {
    if (!hintsToggle) {
      return;
    }
    hintsToggle.textContent = hintsEnabled ? "Hints: On" : "Hints: Off";
  }

  function normalizeCategory(category) {
    const normalized = String(category || "").trim().toLowerCase();
    return ACTION_BUCKET_ORDER.includes(normalized) ? normalized : "player";
  }

  function setActionButtonsEnabled(enabled) {
    const canUse = Boolean(enabled);
    const buttons = actionsList.querySelectorAll(".action-button");
    buttons.forEach((button) => {
      button.disabled = !canUse;
    });
  }

  function setInputEnabled(enabled) {
    const value = Boolean(enabled);
    const allowCommandInput = value && !gameOver;
    input.disabled = !allowCommandInput;
    sendButton.disabled = !allowCommandInput;
    resetButton.disabled = !value;
    setActionButtonsEnabled(value && initialized && !gameOver);
    if (allowCommandInput) {
      input.focus();
    }
  }

  function cleanActionsHeading(heading) {
    const raw = String(heading || "Available actions").trim();
    const withoutCount = raw.replace(/\(\d+\):?\s*$/, "").trim();
    return withoutCount || "Available actions";
  }

  function renderScreen(screen) {
    terminal.innerHTML = ansiToHtml(screen);
    terminal.scrollTop = 0;
  }

  function appendScreen(screen) {
    const block = ansiToHtml(screen);
    if (!block) {
      return;
    }
    if (terminal.innerHTML) {
      terminal.innerHTML += `\n${block}`;
    } else {
      terminal.innerHTML = block;
    }
    terminal.scrollTop = terminal.scrollHeight;
  }

  function setCombatTint(inCombat) {
    document.body.classList.toggle("combat-active", Boolean(inCombat));
  }

  function createStatusSection(label, valueText, listItems = null) {
    const section = document.createElement("section");
    section.className = "status-section";

    const heading = document.createElement("h3");
    heading.className = "status-label";
    heading.textContent = label;
    section.appendChild(heading);

    if (Array.isArray(listItems)) {
      const list = document.createElement("ul");
      list.className = "status-list";
      for (const raw of listItems) {
        const item = document.createElement("li");
        item.textContent = String(raw || "").trim() || "-";
        list.appendChild(item);
      }
      section.appendChild(list);
      return section;
    }

    const value = document.createElement("p");
    value.className = "status-value";
    value.textContent = String(valueText || "-");
    section.appendChild(value);
    return section;
  }

  function renderStatusPanel(panelData) {
    if (!statusPanel || !statusEmpty) {
      return;
    }

    statusPanel.replaceChildren();
    const data = panelData && typeof panelData === "object" ? panelData : null;
    if (!data) {
      statusEmpty.hidden = false;
      statusEmpty.textContent = "Status unavailable.";
      return;
    }

    const levelLine = `Level ${data.level || 1}  ${data.player_name || "Wanderer"}${
      data.quest_title ? `  |  Quest: ${data.quest_title}` : ""
    }`;
    const healthLine = `${data.hp || 0}/${data.max_hp || 0}  ${data.hp_bar || ""}`.trim();
    const skillItems = Array.isArray(data.skills) && data.skills.length ? data.skills : ["None learned yet"];
    const equippedItems =
      Array.isArray(data.equipped) && data.equipped.length ? data.equipped : ["No equipment"];
    const inventoryItems =
      Array.isArray(data.inventory) && data.inventory.length ? data.inventory : ["Inventory is empty"];

    statusPanel.appendChild(createStatusSection("Level", levelLine));
    statusPanel.appendChild(createStatusSection("Health", healthLine));
    statusPanel.appendChild(createStatusSection("Skills", "", skillItems));
    statusPanel.appendChild(createStatusSection("Equipped", "", equippedItems));
    statusPanel.appendChild(createStatusSection("Inventory", "", inventoryItems));

    statusEmpty.hidden = true;
  }

  function renderArt(payload) {
    if (!artPanel || !artTitle) {
      return;
    }
    const title = String(payload?.art_title || "Scene Art").trim() || "Scene Art";
    const ascii = String(payload?.art_ascii || "").replaceAll("\r", "");
    const imageSrc = String(payload?.art_image || "").trim();
    artTitle.textContent = title;

    if (artImage) {
      if (imageSrc) {
        artImage.src = imageSrc;
        artImage.alt = title;
        artImage.hidden = false;
        artPanel.hidden = true;
        return;
      }
      artImage.hidden = true;
      artImage.removeAttribute("src");
      artImage.alt = "";
      artPanel.hidden = false;
    }

    artPanel.textContent = ascii || "(no art available)";
    artPanel.scrollTop = 0;
  }

  function priorityScore(rawValue) {
    const num = Number(rawValue);
    if (!Number.isFinite(num)) {
      return 0;
    }
    return num;
  }

  function sortRowsByPriority(rows) {
    return [...rows].sort((a, b) => {
      if (b.priorityScore !== a.priorityScore) {
        return b.priorityScore - a.priorityScore;
      }
      return a.command.localeCompare(b.command);
    });
  }

  function bucketOrderForRows(rows) {
    const hasTopPlayerAction = rows.some((row) => row.category === "player" && row.priorityScore >= 100);
    if (!hasTopPlayerAction) {
      return ACTION_BUCKET_ORDER;
    }
    return ["player", "movement", "combat", "quest"];
  }

  function renderActionItem(row, isGameOver = false) {
    const item = document.createElement("div");
    item.className = "actions-item";

    const actionButton = document.createElement("button");
    actionButton.type = "button";
    actionButton.className = "action-button";
    actionButton.dataset.command = row.command;
    actionButton.disabled = !initialized || busy || isGameOver;

    const commandNode = document.createElement("code");
    commandNode.className = "action-command";

    const verbNode = document.createElement("span");
    verbNode.className = "action-verb";
    verbNode.textContent = row.verb || row.command;
    commandNode.appendChild(verbNode);

    if (row.argument) {
      commandNode.appendChild(document.createTextNode(" "));
      const argumentNode = document.createElement("span");
      argumentNode.className = "action-argument";
      if (row.argumentColor) {
        argumentNode.classList.add(row.argumentColor);
      }
      argumentNode.textContent = row.argument;
      commandNode.appendChild(argumentNode);
    }

    const descriptionNode = document.createElement("p");
    descriptionNode.className = "action-description";
    descriptionNode.textContent = row.description;
    actionButton.append(commandNode, descriptionNode);

    if (row.hintReason) {
      const reasonNode = document.createElement("p");
      reasonNode.className = "action-hint-reason";
      reasonNode.textContent = row.hintReason;
      actionButton.appendChild(reasonNode);
    }

    item.appendChild(actionButton);
    return item;
  }

  function renderActionGroup(fragment, title, rows, isGameOver = false, isHint = false) {
    if (!rows.length) {
      return;
    }
    const group = document.createElement("section");
    group.className = "actions-group";

    const groupTitle = document.createElement("h3");
    groupTitle.className = `actions-group-title${isHint ? " actions-group-hint" : ""}`;
    groupTitle.textContent = title;

    const groupList = document.createElement("div");
    groupList.className = "actions-group-list";
    for (const row of rows) {
      groupList.appendChild(renderActionItem(row, isGameOver));
    }

    group.append(groupTitle, groupList);
    fragment.appendChild(group);
  }

  function parseActionRows(actions) {
    const rows = [];
    for (const raw of Array.isArray(actions) ? actions : []) {
      const command = String(raw?.command || "").trim();
      if (!command) {
        continue;
      }
      const description = String(raw?.description || "").trim() || "No description.";
      const verb = String(raw?.verb || command.split(/\s+/, 1)[0] || "").trim();
      const argument =
        String(raw?.argument || "").trim() || (command.length > verb.length ? command.slice(verb.length).trim() : "");
      const argumentColor = String(raw?.argument_color || "").trim();
      rows.push({
        command,
        description,
        verb,
        argument,
        argumentColor,
        category: normalizeCategory(raw?.category),
        priorityScore: priorityScore(raw?.priority_score),
        hintReason: "",
      });
    }
    return rows;
  }

  function renderActions(heading, actions, hintRows = [], isGameOver = false) {
    actionsTitle.textContent = cleanActionsHeading(heading);
    actionsList.replaceChildren();

    const rows = parseActionRows(actions);
    if (!rows.length) {
      actionsEmpty.hidden = false;
      actionsEmpty.textContent = isGameOver
        ? "No actions available. Start a new game."
        : "No actions available right now.";
      return;
    }

    const byCommand = new Map(rows.map((row) => [row.command, row]));
    const prioritizedUniqueHints = [];
    const seenHintCommands = new Set();
    for (const raw of Array.isArray(hintRows) ? hintRows : []) {
      const command = String(raw?.command || "").trim();
      if (!command || seenHintCommands.has(command)) {
        continue;
      }
      const base = byCommand.get(command);
      if (!base) {
        continue;
      }
      seenHintCommands.add(command);
      prioritizedUniqueHints.push({
        ...base,
        hintReason: String(raw?.reason || "").trim(),
      });
    }

    const fragment = document.createDocumentFragment();
    if (hintsEnabled && prioritizedUniqueHints.length) {
      renderActionGroup(fragment, "Recommended", prioritizedUniqueHints, isGameOver, true);
    }

    const sortedRows = sortRowsByPriority(rows);
    const grouped = new Map(ACTION_BUCKET_ORDER.map((bucket) => [bucket, []]));
    for (const row of sortedRows) {
      grouped.get(row.category).push(row);
    }

    const bucketOrder = bucketOrderForRows(sortedRows);
    for (const bucket of bucketOrder) {
      const bucketRows = grouped.get(bucket) || [];
      if (!bucketRows.length) {
        continue;
      }
      renderActionGroup(fragment, ACTION_BUCKET_LABEL[bucket] || bucket, bucketRows, isGameOver, false);
    }

    actionsList.appendChild(fragment);
    actionsEmpty.hidden = true;
  }

  function renderPayload(payload, options = {}) {
    const appendOnly = Boolean(options.appendOnly);
    lastPayload = payload;
    if (appendOnly) {
      appendScreen(payload.screen);
    } else {
      renderScreen(payload.screen);
    }
    renderStatusPanel(payload.status_panel);
    renderArt(payload);
    renderActions(payload.actions_heading, payload.actions, payload.hints, Boolean(payload.game_over));
    setCombatTint(payload.in_combat);
  }

  function parsePayload(payload) {
    const jsonText = String(payload || "");
    return JSON.parse(jsonText);
  }

  function persistGameState() {
    if (!api || typeof api.save !== "function") {
      return;
    }
    try {
      const snapshot = String(api.save() || "");
      if (snapshot) {
        writeSavedGame(snapshot);
      }
    } catch (error) {
      console.error("Failed to persist save state.", error);
    }
  }

  function tryRestoreSavedGame() {
    const snapshot = readSavedGame();
    if (!snapshot || !api || typeof api.load !== "function") {
      return { restored: false, payload: null, invalid: false };
    }

    try {
      const result = parsePayload(api.load(snapshot));
      if (result && result.ok && result.payload) {
        return { restored: true, payload: result.payload, invalid: false };
      }
    } catch (error) {
      console.error("Failed to load saved game.", error);
    }

    clearSavedGame();
    return { restored: false, payload: null, invalid: true };
  }

  async function ensurePyodideLoader() {
    if (typeof window.loadPyodide === "function") {
      return;
    }
    await new Promise((resolve, reject) => {
      const script = document.createElement("script");
      script.src = PYODIDE_JS_URL;
      script.async = true;
      script.onload = resolve;
      script.onerror = () => reject(new Error("Unable to load Pyodide runtime."));
      document.head.appendChild(script);
    });
  }

  async function fetchSource(path) {
    const response = await fetch(path, { cache: "no-store" });
    if (!response.ok) {
      throw new Error(`Unable to load ${path}`);
    }
    return response.text();
  }

  function ensureParentDirectory(path) {
    const slash = path.lastIndexOf("/");
    if (slash <= 0) {
      return;
    }
    const directory = path.slice(0, slash);
    const analyzed = pyodide.FS.analyzePath(directory);
    if (!analyzed.exists) {
      pyodide.FS.mkdirTree(directory);
    }
  }

  async function loadGameSources() {
    for (const sourcePath of SOURCE_FILES) {
      const source = await fetchSource(sourcePath);
      ensureParentDirectory(sourcePath);
      pyodide.FS.writeFile(sourcePath, source, { encoding: "utf8" });
    }
  }

  async function bootstrapGameApi() {
    const bootstrapCode = String.raw`
import base64
import json
import os
import pickle
from pathlib import Path

os.environ["BYTE_WORLD_AI_FORCE_COLOR"] = "1"
os.environ["BYTE_WORLD_AI_NO_CLEAR"] = "1"

from content.enemies import ENEMIES
from content.items import EQUIPMENT_SLOT_BY_TYPE, ITEMS
from content.world import LOCATIONS, NPCS
from game.engine import Engine
from game import ui
from game.state import Encounter, clamp_player_hp, create_initial_state, get_effective_stats
from systems import quest

_engine = Engine()
_state = create_initial_state()
_current_art_title = "Scene Art"
_current_art_ascii = ""
_current_art_image = ""

def _load_ascii_art(path: str) -> str:
    try:
        raw = Path(path).read_text(encoding="utf-8")
    except Exception:
        return ""

    lines = [line.rstrip("\r") for line in raw.splitlines()]
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    return "\n".join(lines)

_OLD_SHACK_WISE_OLD_MAN_ASCII = _load_ascii_art("content/art/ascii-art.txt")

_LOCATION_GLYPHS: dict[str, list[str]] = {
    "old_shack": [
        "           /\\",
        "          /  \\",
        "         /____\\",
        "        | []  |",
        "        |_____|",
    ],
    "forest": [
        "      ^^   ^^   ^^",
        "     ^^^  ^^^  ^^^",
        "       ||   ||   ||",
        "       ||   ||   ||",
    ],
    "swamp": [
        "     ~~~  ~~~  ~~~",
        "   ~~  ~~~~  ~~  ~~",
        "      (  o_o  )",
    ],
    "underground_tunnel": [
        "   ####################",
        "  ##                  ##",
        " ##      TUNNEL        ##",
        "  ##                  ##",
        "   ####################",
    ],
    "mountain_base": [
        "        /\\",
        "       /  \\   /\\",
        "      / /\\ \\ /  \\",
        "     /_/  \\_/ /\\ \\",
    ],
    "abandoned_mine": [
        "     ||==========||",
        "     ||   MINE   ||",
        "     ||==========||",
        "        /  __  /",
    ],
    "mountain_peak": [
        "            /\\",
        "           /  \\",
        "          / /\\ \\",
        "         /_/  \\_\\",
    ],
    "mountain_cave": [
        "      _____________",
        "   __/             \\__",
        "  /   GOLD & BONES    \\",
        " /_____________________\\",
    ],
    "desolate_road": [
        "      ||         ||",
        "      ||   ROAD  ||",
        "    ==||=========||==",
        "      ||         ||",
    ],
    "royal_yard": [
        "        |>|",
        "       /###\\",
        "      |#####|",
        "      |#####|",
    ],
    "black_hall": [
        "     || || || || ||",
        "     || || || || ||",
        "     || || || || ||",
        "       BLACK HALL",
    ],
    "dungeon": [
        "     |||||||||||||||",
        "     |  [======]   |",
        "     |   DUNGEON   |",
        "     |||||||||||||||",
    ],
    "witch_terrace": [
        "        (  *  )",
        "      *  (###)  *",
        "        _/___\\_",
        "       /  RUNE  \\",
    ],
}

_NPC_GLYPHS: dict[str, list[str]] = {
    "wise_old_man": [
        "        .-''''-.",
        "      /  .--.   \\",
        "     |  (o  o)   |",
        "     |    __     |",
        "      \\  '--'   /",
        "       '------'",
    ],
    "elle": [
        "      .-''''-.",
        "     /  .--.  \\",
        "    |  (o  o)  |",
        "    |   __     |",
        "    |  /__\\    |",
        "     \\        /",
    ],
}

_BOSS_GLYPHS: list[str] = [
    "      /\\  /\\  /\\",
    "     /  \\/  \\/  \\",
    "    |   B O S S  |",
    "    |   HUNTER   |",
    "     \\__________/",
]

_CREATURE_GLYPHS: list[str] = [
    "        /\\_/\\",
    "       ( o.o )",
    "        > ^ <",
    "      CREATURE",
]

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
_SKILL_TERMS = {
    "attack",
    "defense",
    "health",
    "focus strike",
    "guard stance",
    "second wind",
}
_QUEST_STEPS = {
    "awakening": "Talk to the Wise Old Man and learn the core path.",
    "swamp_secret": "Defeat the swamp boss to recover the hidden key.",
    "mountain_flame": "Reach Dragon Mountain and defeat the dragon.",
    "castle_road": "Push toward Makor's Castle and survive the goblin road.",
    "black_hall": "Defeat King Makor in the dungeon below Black Hall.",
    "witch_bane": "Defeat the Onyx Witch and break her hold.",
    "rescue_elle": "Free and cleanse Elle to complete the story.",
    "homecoming": "Return to the Old Shack and close remaining threads.",
}
_NPC_COLOR_BY_NAME = {
    npc.get("name", "").strip().lower(): "ansi-blue"
    for npc in NPCS.values()
    if npc.get("name")
}

_ENEMY_COLOR_BY_NAME: dict[str, str] = {}
for _enemy_id, _enemy in ENEMIES.items():
    _enemy_name = _enemy.get("name", "").strip().lower()
    if not _enemy_name:
        continue
    if _enemy_id in _END_BOSS_IDS:
        _ENEMY_COLOR_BY_NAME[_enemy_name] = "ansi-red"
    elif _enemy.get("category") == "boss":
        _ENEMY_COLOR_BY_NAME[_enemy_name] = "ansi-orange"
    else:
        _ENEMY_COLOR_BY_NAME[_enemy_name] = "ansi-yellow"

_ITEM_COLOR_BY_NAME: dict[str, str] = {}
for _item_id, _item in ITEMS.items():
    _item_name = _item.get("name", "").strip().lower()
    if not _item_name:
        continue
    _is_rare = _item_id in _IMPORTANT_OR_RARE_ITEM_IDS or _item.get("type") in {"quest", "key", "boon"}
    _ITEM_COLOR_BY_NAME[_item_name] = "ansi-purple" if _is_rare else "ansi-green"

def _normalize_token(text: str) -> str:
    return "".join(ch for ch in str(text or "").strip().lower() if ch.isalnum() or ch.isspace())

def _item_power_tuple(item_id: str | None) -> tuple[float, int, int, int, int]:
    if not item_id:
        return (-9999.0, -9999, -9999, -9999, -9999)
    item = ITEMS.get(item_id, {})
    attack = int(item.get("attack_bonus", 0))
    defense = int(item.get("defense_bonus", 0))
    max_hp = int(item.get("max_hp_bonus", 0))
    value = int(item.get("value", 0))
    normalized = attack + defense + (max_hp / 3.0)
    return (normalized, attack, defense, max_hp, value)

def _inventory_item_id_from_argument(argument: str) -> str | None:
    query = _normalize_token(argument)
    if not query:
        return None

    for item_id in _state.player.inventory:
        item_name = ITEMS.get(item_id, {}).get("name", item_id)
        if query in {_normalize_token(item_id), _normalize_token(item_name)}:
            return item_id
    return None

def _equipped_upgrade_for_item(item_id: str) -> bool:
    item = ITEMS.get(item_id, {})
    slot = EQUIPMENT_SLOT_BY_TYPE.get(item.get("type", ""))
    if not slot:
        return False
    current_id = _state.player.equipment.get(slot)
    return _item_power_tuple(item_id) > _item_power_tuple(current_id)

def _is_equip_upgrade_action(action: dict) -> bool:
    if action["verb_lower"] != "equip":
        return False
    arg = action["argument"].strip().lower()
    if arg == "all":
        return _has_any_gear_upgrade()
    item_id = _inventory_item_id_from_argument(action["argument"])
    if not item_id:
        return False
    return _equipped_upgrade_for_item(item_id)

def _has_any_gear_upgrade() -> bool:
    for item_id in _state.player.inventory:
        item = ITEMS.get(item_id, {})
        if item.get("type", "") not in EQUIPMENT_SLOT_BY_TYPE:
            continue
        if _equipped_upgrade_for_item(item_id):
            return True
    return False

def _is_context_quest_item_action(action: dict) -> bool:
    if action["verb_lower"] not in {"use", "read"}:
        return False
    arg = _normalize_token(action["argument"])
    if arg == "goblin riddle" and _state.active_encounter and _state.active_encounter.enemy_id == "onyx_witch":
        return bool(_state.active_encounter.witch_barrier_active)
    if arg == "crusty key":
        return (
            _state.current_location_id == "witch_terrace"
            and "onyx_witch_defeated" in _state.flags
            and "elle_freed" not in _state.flags
        )
    if arg == "vial of tears":
        return (
            _state.current_location_id == "witch_terrace"
            and "elle_freed" in _state.flags
            and "elle_cleansed" not in _state.flags
        )
    if arg == "hoard of treasure":
        return _state.current_location_id == "old_shack" and "hoard_delivered" not in _state.flags
    return False

def _is_heal_action(action: dict) -> bool:
    if action["verb_lower"] != "use":
        return False
    item_id = _inventory_item_id_from_argument(action["argument"])
    if not item_id:
        return False
    return ITEMS.get(item_id, {}).get("type") == "consumable"

def _recommended_move_command() -> str | None:
    target_id, direction = _engine._recommended_map_step(_state)
    if not target_id or not direction:
        return None
    return f"move {direction}"

def _boxed_art(title: str, glyph_lines: list[str]) -> str:
    clean_title = str(title or "Unknown")
    lines = [str(line).rstrip() for line in glyph_lines if str(line).strip()]
    if not lines:
        lines = ["(no art)"]
    width = max(len(clean_title), *(len(line) for line in lines))
    border = "+" + "-" * (width + 2) + "+"
    output = [border, f"| {clean_title.ljust(width)} |", border]
    for line in lines:
        output.append(f"| {line.ljust(width)} |")
    output.append(border)
    return "\n".join(output)

def _location_art(location_id: str) -> tuple[str, str]:
    loc = LOCATIONS.get(location_id, {})
    title = loc.get("name", str(location_id))
    if location_id == "old_shack" and _OLD_SHACK_WISE_OLD_MAN_ASCII:
        return title, _OLD_SHACK_WISE_OLD_MAN_ASCII
    glyph = _LOCATION_GLYPHS.get(location_id)
    if not glyph:
        glyph = [
            "       _________",
            "      /  ZONE  /|",
            "     /________/ |",
            "     |        | |",
            "     |________|/",
        ]
    return title, _boxed_art(title, glyph)

def _npc_art(npc_id: str) -> tuple[str, str]:
    npc = NPCS.get(npc_id, {})
    title = npc.get("name", npc_id)
    if npc_id == "wise_old_man" and _state.current_location_id == "old_shack" and _OLD_SHACK_WISE_OLD_MAN_ASCII:
        return title, _OLD_SHACK_WISE_OLD_MAN_ASCII
    glyph = _NPC_GLYPHS.get(npc_id, _NPC_GLYPHS.get("wise_old_man", []))
    return title, _boxed_art(title, glyph)

def _enemy_art(enemy_id: str) -> tuple[str, str]:
    enemy = ENEMIES.get(enemy_id, {})
    title = enemy.get("name", enemy_id)
    if enemy.get("category") == "boss":
        glyph = _BOSS_GLYPHS
    else:
        glyph = _CREATURE_GLYPHS
    return title, _boxed_art(title, glyph)

def _set_art(title: str, ascii_text: str, image_url: str = "") -> None:
    global _current_art_title, _current_art_ascii, _current_art_image
    _current_art_title = str(title or "Scene Art")
    _current_art_ascii = str(ascii_text or "").strip("\n")
    _current_art_image = str(image_url or "").strip()

def _matching_npc_id_from_command(command_text: str) -> str | None:
    if not command_text.startswith("talk "):
        return None
    query = _normalize_token(command_text[5:])
    if not query:
        return None
    location = LOCATIONS.get(_state.current_location_id, {})
    for npc_id in location.get("npcs", []):
        if npc_id == "elle" and "onyx_witch_defeated" not in _state.flags:
            continue
        npc_name = _normalize_token(NPCS.get(npc_id, {}).get("name", npc_id))
        if query == _normalize_token(npc_id) or query == npc_name or query in npc_name:
            return npc_id
    return None

def _status_panel_payload() -> dict:
    stats = get_effective_stats(_state.player)
    objective = quest.get_current_objective(_state)
    hp_bar = ui.health_bar(_state.player.hp, stats["max_hp"])

    equipped_lines = []
    for slot, item_id in _state.player.equipment.items():
        item_name = ITEMS.get(item_id, {}).get("name", item_id) if item_id else "none"
        equipped_lines.append(f"{slot.title()}: {item_name}")

    inventory_lines = []
    for item_id, qty in sorted(_state.player.inventory.items()):
        item = ITEMS.get(item_id, {})
        item_name = item.get("name", item_id)
        item_type = item.get("type", "unknown")
        inventory_lines.append(f"{item_name} x{qty} ({item_type})")

    return {
        "player_name": _state.player.name,
        "level": int(_state.player.level),
        "hp": int(_state.player.hp),
        "max_hp": int(stats["max_hp"]),
        "hp_bar": hp_bar,
        "skills": sorted(_state.player.skills),
        "equipped": equipped_lines,
        "inventory": inventory_lines,
        "quest_title": objective.get("title", ""),
    }

def _encode_rng_state() -> str:
    state_bytes = pickle.dumps(_state.rng.getstate())
    return base64.b64encode(state_bytes).decode("ascii")

def _decode_rng_state(encoded: str) -> tuple | None:
    try:
        data = base64.b64decode(encoded.encode("ascii"))
        return pickle.loads(data)
    except Exception:
        return None

def _state_to_dict() -> dict:
    encounter_payload = None
    if _state.active_encounter:
        encounter = _state.active_encounter
        encounter_payload = {
            "enemy_id": encounter.enemy_id,
            "current_hp": int(encounter.current_hp),
            "intent_index": int(encounter.intent_index),
            "player_defending": bool(encounter.player_defending),
            "special_phase": str(encounter.special_phase),
            "witch_barrier_active": bool(encounter.witch_barrier_active),
            "turn_count": int(encounter.turn_count),
        }

    return {
        "schema_version": 1,
        "player": {
            "name": _state.player.name,
            "base_max_hp": int(_state.player.base_max_hp),
            "base_attack": int(_state.player.base_attack),
            "base_defense": int(_state.player.base_defense),
            "hp": int(_state.player.hp),
            "xp": int(_state.player.xp),
            "level": int(_state.player.level),
            "skill_points": int(_state.player.skill_points),
            "gold": int(_state.player.gold),
            "inventory": {str(k): int(v) for k, v in _state.player.inventory.items()},
            "equipment": {str(k): (str(v) if v else None) for k, v in _state.player.equipment.items()},
            "skills": sorted(str(skill) for skill in _state.player.skills),
            "cooldowns": {str(k): int(v) for k, v in _state.player.cooldowns.items()},
            "titles": [str(title) for title in _state.player.titles],
            "temporary_bonuses": {str(k): int(v) for k, v in _state.player.temporary_bonuses.items()},
        },
        "current_location_id": str(_state.current_location_id),
        "quest_stage": str(_state.quest_stage),
        "flags": sorted(str(flag) for flag in _state.flags),
        "active_encounter": encounter_payload,
        "discovered_locations": sorted(str(loc) for loc in _state.discovered_locations),
        "turn_count": int(_state.turn_count),
        "game_over": bool(_state.game_over),
        "victory": bool(_state.victory),
        "rng_state": _encode_rng_state(),
    }

def _restore_state(raw: dict) -> bool:
    global _state
    try:
        player_raw = raw.get("player")
        if not isinstance(player_raw, dict):
            return False

        restored = create_initial_state()
        player = restored.player

        player.name = str(player_raw.get("name", player.name))
        player.base_max_hp = int(player_raw.get("base_max_hp", player.base_max_hp))
        player.base_attack = int(player_raw.get("base_attack", player.base_attack))
        player.base_defense = int(player_raw.get("base_defense", player.base_defense))
        player.hp = int(player_raw.get("hp", player.hp))
        player.xp = int(player_raw.get("xp", player.xp))
        player.level = int(player_raw.get("level", player.level))
        player.skill_points = int(player_raw.get("skill_points", player.skill_points))
        player.gold = int(player_raw.get("gold", player.gold))
        player.inventory = {
            str(k): max(0, int(v))
            for k, v in dict(player_raw.get("inventory", {})).items()
        }
        equipment_map = dict(player.equipment)
        for k, v in dict(player_raw.get("equipment", {})).items():
            equipment_map[str(k)] = str(v) if v else None
        player.equipment = equipment_map
        player.skills = {str(skill) for skill in player_raw.get("skills", [])}
        player.cooldowns = {
            str(k): max(0, int(v))
            for k, v in dict(player_raw.get("cooldowns", {})).items()
        }
        player.titles = [str(title) for title in player_raw.get("titles", [])]
        player.temporary_bonuses = {
            str(k): int(v)
            for k, v in dict(player_raw.get("temporary_bonuses", {})).items()
        }
        clamp_player_hp(player)

        restored.current_location_id = str(raw.get("current_location_id", restored.current_location_id))
        if restored.current_location_id not in LOCATIONS:
            restored.current_location_id = "old_shack"

        restored.quest_stage = str(raw.get("quest_stage", restored.quest_stage))
        if restored.quest_stage not in _QUEST_STEPS:
            restored.quest_stage = "awakening"
        restored.flags = {str(flag) for flag in raw.get("flags", [])}

        encounter_raw = raw.get("active_encounter")
        if isinstance(encounter_raw, dict):
            restored.active_encounter = Encounter(
                enemy_id=str(encounter_raw.get("enemy_id", "")),
                current_hp=max(0, int(encounter_raw.get("current_hp", 0))),
                intent_index=max(0, int(encounter_raw.get("intent_index", 0))),
                player_defending=bool(encounter_raw.get("player_defending", False)),
                special_phase=str(encounter_raw.get("special_phase", "combat")),
                witch_barrier_active=bool(encounter_raw.get("witch_barrier_active", False)),
                turn_count=max(0, int(encounter_raw.get("turn_count", 0))),
            )
            if restored.active_encounter.enemy_id not in ENEMIES:
                restored.active_encounter = None
        else:
            restored.active_encounter = None

        discovered = {str(loc) for loc in raw.get("discovered_locations", [])}
        if restored.current_location_id:
            discovered.add(restored.current_location_id)
        restored.discovered_locations = discovered
        restored.turn_count = max(0, int(raw.get("turn_count", restored.turn_count)))
        restored.game_over = bool(raw.get("game_over", False))
        restored.victory = bool(raw.get("victory", False))

        rng_state_raw = raw.get("rng_state")
        if isinstance(rng_state_raw, str) and rng_state_raw:
            decoded = _decode_rng_state(rng_state_raw)
            if decoded is not None:
                restored.rng.setstate(decoded)

        max_hp = max(1, get_effective_stats(restored.player)["max_hp"])
        restored.player.hp = max(0, min(int(restored.player.hp), max_hp))

        _state = restored
        return True
    except Exception:
        return False

def _resume_screen() -> str:
    resume_messages = ["Saved game loaded from your browser."]
    if _state.active_encounter:
        enemy_id = _state.active_encounter.enemy_id
        enemy_name = ENEMIES.get(enemy_id, {}).get("name", enemy_id)
        resume_messages.append(f"Encounter in progress: {enemy_name}.")
    else:
        location_name = LOCATIONS.get(_state.current_location_id, {}).get("name", _state.current_location_id)
        resume_messages.append(f"Current location: {location_name}.")
    return _engine._render_screen(_state, action_messages=resume_messages)

def _action_category(command: str) -> str:
    verb = command.split(" ", 1)[0].strip().lower() if command else ""
    if verb == "move":
        return "movement"
    if verb in {"fight", "defend", "skill", "run", "joke", "bribe", "hunt"}:
        return "combat"
    if verb in {"quest", "talk", "map"}:
        return "quest"
    if verb in {"use", "read"} and _state.active_encounter:
        return "combat"
    return "player"

def _argument_color(verb: str, argument: str) -> str:
    arg = argument.strip().lower()
    if not arg:
        return ""

    if verb == "talk":
        return _NPC_COLOR_BY_NAME.get(arg, "ansi-blue")
    if verb == "skill":
        return "ansi-pink"
    if verb == "train":
        stat = arg.split(" ", 1)[0]
        if stat in {"attack", "defense", "health"}:
            return "ansi-pink"
        return ""
    if verb in {"use", "equip", "read"}:
        if arg in {"all", "a,b,c"}:
            return ""
        return _ITEM_COLOR_BY_NAME.get(arg, "ansi-green")
    if verb == "fight" and arg:
        return _ENEMY_COLOR_BY_NAME.get(arg, "ansi-yellow")

    if arg in _SKILL_TERMS:
        return "ansi-pink"
    if arg in _NPC_COLOR_BY_NAME:
        return "ansi-blue"
    if arg in _ENEMY_COLOR_BY_NAME:
        return _ENEMY_COLOR_BY_NAME[arg]
    if arg in _ITEM_COLOR_BY_NAME:
        return _ITEM_COLOR_BY_NAME[arg]
    return ""

def _action_priority(action: dict) -> int:
    command = action["command"]
    verb = action["verb_lower"]
    score = 40

    if verb == "train":
        score = 220
        if command == "train all":
            score = 235
        return score

    if verb == "equip":
        if _is_equip_upgrade_action(action):
            if action["argument"].strip().lower() == "all":
                return 225
            return 215
        return 6

    if _is_context_quest_item_action(action):
        return 205

    if _state.active_encounter:
        hp_ratio = _state.player.hp / max(1, get_effective_stats(_state.player)["max_hp"])
        if verb == "read" and _normalize_token(action["argument"]) == "goblin riddle":
            return 230 if _is_context_quest_item_action(action) else 85
        if _is_heal_action(action):
            return 210 if hp_ratio <= 0.45 else 120
        if command == "skill focus strike":
            return 180
        if verb == "fight":
            return 165
        if verb == "defend":
            return 120
        if verb == "run":
            return 160 if hp_ratio <= 0.3 else 75
        if verb in {"joke", "bribe"}:
            return 170
        return 60

    if command == _recommended_move_command():
        score = max(score, 175)
    elif verb == "move":
        score = max(score, 55)

    if command == "talk wise old man" and "met_old_man" not in _state.flags:
        score = max(score, 185)

    if verb == "hunt":
        score = max(score, 78)

    if command == "quest":
        score = max(score, 95)
    if command == "status":
        score = max(score, 90)
    if command == "map":
        score = max(score, 88)
    if command == "look":
        score = max(score, 70)
    if _is_heal_action(action):
        hp_ratio = _state.player.hp / max(1, get_effective_stats(_state.player)["max_hp"])
        score = max(score, 120 if hp_ratio <= 0.5 else 45)

    return score

def _find_action(actions: list[dict], command: str) -> dict | None:
    for action in actions:
        if action["command"] == command:
            return action
    return None

def _find_actions_by_prefix(actions: list[dict], prefix: str) -> list[dict]:
    return [action for action in actions if action["command"].startswith(prefix)]

def _add_hint(hints: list[dict[str, str]], seen: set[str], action: dict | None, reason: str) -> None:
    if not action:
        return
    command = action["command"]
    if command in seen:
        return
    seen.add(command)
    hints.append({"command": command, "reason": reason})

def _hint_recommendations(actions: list[dict]) -> list[dict[str, str]]:
    if _state.game_over:
        return []

    hints: list[dict[str, str]] = []
    seen: set[str] = set()

    if _state.active_encounter:
        encounter = _state.active_encounter
        max_hp = max(1, get_effective_stats(_state.player)["max_hp"])
        hp_ratio = _state.player.hp / max_hp

        if encounter.special_phase == "negotiation":
            _add_hint(hints, seen, _find_action(actions, "joke"), "Safest no-cost path through goblin negotiation.")
            _add_hint(hints, seen, _find_action(actions, "bribe"), "Fallback escape if you want to avoid full combat.")
            _add_hint(hints, seen, _find_action(actions, "fight"), "Choose if you want rewards and combat progression.")
            return hints[:4]

        if encounter.enemy_id == "onyx_witch" and encounter.witch_barrier_active:
            _add_hint(
                hints,
                seen,
                _find_action(actions, "read goblin riddle") or _find_action(actions, "use goblin riddle"),
                "Break the witch barrier first so your attacks can land.",
            )

        if hp_ratio <= 0.45:
            heal_actions = [action for action in actions if _is_heal_action(action)]
            heal_actions.sort(key=lambda action: action["priority_score"], reverse=True)
            _add_hint(hints, seen, heal_actions[0] if heal_actions else None, "Stabilize HP before taking more hits.")

        _add_hint(
            hints,
            seen,
            _find_action(actions, "skill focus strike"),
            "High burst damage keeps encounters shorter.",
        )
        _add_hint(hints, seen, _find_action(actions, "fight"), "Maintain pressure when no special counter is needed.")
        if hp_ratio <= 0.3:
            _add_hint(hints, seen, _find_action(actions, "run"), "High risk state. Escape can preserve the run.")
        return hints[:4]

    if _state.player.skill_points > 0:
        train_cmd = "train all" if _state.player.skill_points >= 3 else "train attack 1"
        _add_hint(
            hints,
            seen,
            _find_action(actions, train_cmd) or (_find_actions_by_prefix(actions, "train ")[0] if _find_actions_by_prefix(actions, "train ") else None),
            "Spend skill points early to improve survivability and damage curve.",
        )

    upgrade_actions = [action for action in actions if _is_equip_upgrade_action(action)]
    upgrade_actions.sort(key=lambda action: action["priority_score"], reverse=True)
    for action in upgrade_actions[:2]:
        _add_hint(hints, seen, action, "Immediate gear upgrade available. Equip now for stronger upcoming fights.")

    if "met_old_man" not in _state.flags:
        _add_hint(
            hints,
            seen,
            _find_action(actions, "talk wise old man"),
            "This unlocks your core combat skills and main quest flow.",
        )

    for command, reason in [
        ("use crusty key", "Unlock Elle after the witch fight."),
        ("use vial of tears", "Cleanse Elle to finish the main storyline."),
        ("use hoard of treasure", "Turn in treasure at the shack for bonus gold."),
    ]:
        action = _find_action(actions, command)
        if action and _is_context_quest_item_action(action):
            _add_hint(hints, seen, action, reason)

    move_command = _recommended_move_command()
    if move_command:
        _add_hint(
            hints,
            seen,
            _find_action(actions, move_command),
            f"Recommended quest path: {_QUEST_STEPS.get(_state.quest_stage, 'Advance main progression')}",
        )
    _add_hint(hints, seen, _find_action(actions, "quest"), "Check objective text if you are unsure about next steps.")
    _add_hint(hints, seen, _find_action(actions, "status"), "Review HP and stat readiness before moving on.")

    return hints[:5]

def _action_payload() -> tuple[str, list[dict], list[dict[str, str]]]:
    if _state.game_over:
        return "Available actions (0):", [], []

    lines = _engine._build_input_hints(_state)
    if not lines:
        return "Available actions (0):", [], []

    heading = str(lines[0])
    actions: list[dict[str, str]] = []
    for raw in lines[1:]:
        line = str(raw).strip()
        if not line or ":" not in line:
            continue
        command, description = line.split(":", 1)
        action_command = command.strip()
        command_parts = action_command.split(maxsplit=1)
        verb = command_parts[0].strip() if command_parts else action_command
        argument = command_parts[1].strip() if len(command_parts) > 1 else ""
        verb_lower = verb.lower()
        action = {
            "command": action_command,
            "description": description.strip(),
            "category": _action_category(action_command),
            "verb": verb,
            "verb_lower": verb_lower,
            "argument": argument,
            "argument_color": _argument_color(verb_lower, argument),
        }
        action["priority_score"] = _action_priority(action)
        actions.append(action)

    hints = _hint_recommendations(actions)
    cleaned_actions = [
        {
            "command": action["command"],
            "description": action["description"],
            "category": action["category"],
            "verb": action["verb"],
            "argument": action["argument"],
            "argument_color": action["argument_color"],
            "priority_score": int(action["priority_score"]),
        }
        for action in actions
    ]
    return heading, cleaned_actions, hints

def _strip_hint_block(screen: str) -> str:
    if _state.game_over:
        return screen

    hints = ui.format_messages(_engine._build_input_hints(_state))
    if hints and screen.endswith(hints):
        return screen[: -len(hints)].rstrip()
    return screen

def _payload(screen: str) -> str:
    heading, actions, hints = _action_payload()
    return json.dumps(
        {
            "screen": _strip_hint_block(screen),
            "game_over": bool(_state.game_over),
            "in_combat": bool(_state.active_encounter),
            "status_panel": _status_panel_payload(),
            "art_title": _current_art_title,
            "art_ascii": _current_art_ascii,
            "art_image": _current_art_image,
            "actions_heading": heading,
            "actions": actions,
            "hints": hints,
        }
    )

def web_initial() -> str:
    if not _current_art_ascii and not _current_art_image:
        location_title, location_ascii = _location_art(_state.current_location_id)
        _set_art(location_title, location_ascii)
    return _payload(_engine.initial_screen(_state))

def web_process(command: str) -> str:
    command_text = str(command or "").strip().lower()
    previous_location = _state.current_location_id
    previous_discovered = set(_state.discovered_locations)
    previous_encounter_enemy = _state.active_encounter.enemy_id if _state.active_encounter else None

    screen = _engine.process_raw_command(_state, command)

    if _state.active_encounter and previous_encounter_enemy is None:
        enemy_title, enemy_ascii = _enemy_art(_state.active_encounter.enemy_id)
        _set_art(enemy_title, enemy_ascii)
    elif command_text.startswith("talk "):
        npc_id = _matching_npc_id_from_command(command_text)
        if npc_id:
            npc_title, npc_ascii = _npc_art(npc_id)
            _set_art(npc_title, npc_ascii)
    elif (
        command_text.startswith("move ")
        and _state.current_location_id != previous_location
        and _state.current_location_id not in previous_discovered
    ):
        location_title, location_ascii = _location_art(_state.current_location_id)
        _set_art(location_title, location_ascii)

    payload = json.loads(_payload(screen))
    screen_text = str(payload.get("screen", ""))
    payload["append_only_notice"] = bool(
        command_text.startswith("skill") and "is on cooldown for" in screen_text
    )
    return json.dumps(payload)

def web_reset() -> str:
    global _state
    _state = create_initial_state()
    location_title, location_ascii = _location_art(_state.current_location_id)
    _set_art(location_title, location_ascii)
    return _payload(_engine.initial_screen(_state))

def web_save_state() -> str:
    return json.dumps({"version": 1, "state": _state_to_dict()})

def web_load_state(snapshot: str) -> str:
    try:
        payload = json.loads(str(snapshot or ""))
    except Exception:
        return json.dumps({"ok": False, "error": "invalid_json"})

    if not isinstance(payload, dict):
        return json.dumps({"ok": False, "error": "invalid_payload"})

    state_payload = payload.get("state")
    if not isinstance(state_payload, dict):
        return json.dumps({"ok": False, "error": "missing_state"})

    if not _restore_state(state_payload):
        return json.dumps({"ok": False, "error": "restore_failed"})

    if _state.active_encounter:
        enemy_title, enemy_ascii = _enemy_art(_state.active_encounter.enemy_id)
        _set_art(enemy_title, enemy_ascii)
    else:
        location_title, location_ascii = _location_art(_state.current_location_id)
        _set_art(location_title, location_ascii)

    restored_payload = json.loads(_payload(_resume_screen()))
    return json.dumps({"ok": True, "payload": restored_payload})
`;

    await pyodide.runPythonAsync(bootstrapCode);
    api = {
      initial: pyodide.globals.get("web_initial"),
      process: pyodide.globals.get("web_process"),
      reset: pyodide.globals.get("web_reset"),
      save: pyodide.globals.get("web_save_state"),
      load: pyodide.globals.get("web_load_state"),
    };
  }

  async function startGame() {
    setStatus("Loading Python runtime in browser...");
    await ensurePyodideLoader();
    pyodide = await window.loadPyodide();

    setStatus("Loading game files...");
    await loadGameSources();

    setStatus("Starting game engine...");
    await bootstrapGameApi();

    const restoreAttempt = tryRestoreSavedGame();
    const payload = restoreAttempt.payload || parsePayload(api.initial());
    gameOver = Boolean(payload.game_over);
    renderPayload(payload);
    initialized = true;
    persistGameState();

    if (restoreAttempt.restored) {
      if (gameOver) {
        setStatus("Saved game loaded. Game over. Start a new game to continue.", true);
      } else {
        setStatus("Saved game loaded. Enter a command to continue.");
      }
    } else if (restoreAttempt.invalid) {
      setStatus("Saved game could not be restored. Started a new game.");
    } else if (gameOver) {
      setStatus("Game over. Start a new game to continue.", true);
    } else {
      setStatus("Enter a command to continue.");
    }
    input.placeholder = "Type a command (help, move north, fight...)";
    setInputEnabled(true);
  }

  async function handleCommand(command) {
    const payload = parsePayload(api.process(command));
    gameOver = Boolean(payload.game_over);
    renderPayload(payload, { appendOnly: Boolean(payload.append_only_notice) });
    persistGameState();
    if (gameOver) {
      setStatus("Game over. Start a new game to continue.", true);
    } else {
      setStatus("Enter a command to continue.");
    }
  }

  async function handleReset() {
    clearSavedGame();
    const payload = parsePayload(api.reset());
    gameOver = Boolean(payload.game_over);
    renderPayload(payload);
    persistGameState();
    setStatus("New game started.");
  }

  async function runActionCommand(rawCommand, clearInput = false) {
    if (!initialized || busy || gameOver) {
      return;
    }

    const command = String(rawCommand || "").trim();
    if (!command) {
      input.focus();
      return;
    }

    busy = true;
    setInputEnabled(false);
    setStatus("Running command...");
    try {
      await handleCommand(command);
      if (clearInput) {
        input.value = "";
      }
    } catch (error) {
      setStatus("Command failed. Refresh page to recover.", true);
      console.error(error);
    } finally {
      busy = false;
      setInputEnabled(true);
    }
  }

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    await runActionCommand(input.value, true);
  });

  actionsList.addEventListener("click", async (event) => {
    const actionButton = event.target.closest(".action-button");
    if (!actionButton) {
      return;
    }
    const command = actionButton.dataset.command || "";
    await runActionCommand(command, false);
  });

  if (hintsToggle) {
    hintsToggle.addEventListener("click", () => {
      hintsEnabled = !hintsEnabled;
      saveHintsPreference();
      updateHintsToggleLabel();
      if (lastPayload) {
        renderActions(
          lastPayload.actions_heading,
          lastPayload.actions,
          lastPayload.hints,
          Boolean(lastPayload.game_over),
        );
      }
    });
  }

  resetButton.addEventListener("click", async () => {
    if (!initialized || busy) {
      return;
    }
    busy = true;
    setInputEnabled(false);
    setStatus("Starting new game...");
    try {
      await handleReset();
      input.value = "";
    } catch (error) {
      setStatus("Reset failed. Refresh page to recover.", true);
      console.error(error);
    } finally {
      busy = false;
      setInputEnabled(true);
    }
  });

  loadHintsPreference();
  updateHintsToggleLabel();
  setInputEnabled(false);
  startGame().catch((error) => {
    setStatus("Startup failed. Check console for details.", true);
    terminal.textContent = String(error);
    renderActions("Available actions", [], [], false);
    actionsEmpty.textContent = "Unable to load actions.";
    console.error(error);
  });
})();
