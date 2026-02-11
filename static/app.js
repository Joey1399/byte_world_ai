(() => {
  const terminal = document.getElementById("terminal");
  const form = document.getElementById("command-form");
  const input = document.getElementById("command-input");
  const sendButton = document.getElementById("send-button");
  const resetButton = document.getElementById("reset-button");
  const statusLine = document.getElementById("status-line");
  const actionsTitle = document.getElementById("actions-title");
  const actionsList = document.getElementById("actions-list");
  const actionsEmpty = document.getElementById("actions-empty");

  const PYODIDE_JS_URL = "https://cdn.jsdelivr.net/pyodide/v0.29.3/full/pyodide.js";
  const SOURCE_FILES = [
    "content/__init__.py",
    "content/enemies.py",
    "content/items.py",
    "content/quests.py",
    "content/world.py",
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

  let pyodide = null;
  let api = null;
  let busy = false;
  let gameOver = false;
  let initialized = false;

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

  function renderActions(heading, actions, isGameOver = false) {
    actionsTitle.textContent = cleanActionsHeading(heading);
    actionsList.replaceChildren();

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
      const category = normalizeCategory(raw?.category);
      rows.push({
        command,
        description,
        verb,
        argument,
        argumentColor,
        category,
      });
    }

    if (!rows.length) {
      actionsEmpty.hidden = false;
      actionsEmpty.textContent = isGameOver
        ? "No actions available. Start a new game."
        : "No actions available right now.";
      return;
    }

    const grouped = new Map(ACTION_BUCKET_ORDER.map((bucket) => [bucket, []]));
    for (const row of rows) {
      grouped.get(row.category).push(row);
    }

    const fragment = document.createDocumentFragment();
    for (const bucket of ACTION_BUCKET_ORDER) {
      const bucketRows = grouped.get(bucket) || [];
      if (!bucketRows.length) {
        continue;
      }

      const group = document.createElement("section");
      group.className = "actions-group";

      const groupTitle = document.createElement("h3");
      groupTitle.className = "actions-group-title";
      groupTitle.textContent = ACTION_BUCKET_LABEL[bucket] || bucket;

      const groupList = document.createElement("div");
      groupList.className = "actions-group-list";

      for (const row of bucketRows) {
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
        item.appendChild(actionButton);
        groupList.appendChild(item);
      }

      group.append(groupTitle, groupList);
      fragment.appendChild(group);
    }

    actionsList.appendChild(fragment);
    actionsEmpty.hidden = true;
  }

  function renderPayload(payload) {
    renderScreen(payload.screen);
    renderActions(payload.actions_heading, payload.actions, Boolean(payload.game_over));
  }

  function parsePayload(payload) {
    const jsonText = String(payload || "");
    return JSON.parse(jsonText);
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
    const bootstrapCode = `
import json
import os

os.environ["BYTE_WORLD_AI_FORCE_COLOR"] = "1"
os.environ["BYTE_WORLD_AI_NO_CLEAR"] = "1"

from content.enemies import ENEMIES
from content.items import ITEMS
from content.world import NPCS
from game.engine import Engine
from game import ui
from game.state import create_initial_state

_engine = Engine()
_state = create_initial_state()

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

def _action_category(command: str) -> str:
    verb = command.split(" ", 1)[0].strip().lower() if command else ""
    if verb == "move":
        return "movement"
    if verb in {"fight", "defend", "skill", "run", "joke", "bribe"}:
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

def _action_payload() -> tuple[str, list[dict[str, str]]]:
    if _state.game_over:
        return "Available actions (0):", []

    lines = _engine._build_input_hints(_state)
    if not lines:
        return "Available actions (0):", []

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
        actions.append(
            {
                "command": action_command,
                "description": description.strip(),
                "category": _action_category(action_command),
                "verb": verb,
                "argument": argument,
                "argument_color": _argument_color(verb_lower, argument),
            }
        )
    return heading, actions

def _strip_hint_block(screen: str) -> str:
    if _state.game_over:
        return screen

    hints = ui.format_messages(_engine._build_input_hints(_state))
    if hints and screen.endswith(hints):
        return screen[: -len(hints)].rstrip()
    return screen

def _payload(screen: str) -> str:
    heading, actions = _action_payload()
    return json.dumps(
        {
            "screen": _strip_hint_block(screen),
            "game_over": bool(_state.game_over),
            "actions_heading": heading,
            "actions": actions,
        }
    )

def web_initial() -> str:
    return _payload(_engine.initial_screen(_state))

def web_process(command: str) -> str:
    return _payload(_engine.process_raw_command(_state, command))

def web_reset() -> str:
    global _state
    _state = create_initial_state()
    return _payload(_engine.initial_screen(_state))
`;

    await pyodide.runPythonAsync(bootstrapCode);
    api = {
      initial: pyodide.globals.get("web_initial"),
      process: pyodide.globals.get("web_process"),
      reset: pyodide.globals.get("web_reset"),
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

    const payload = parsePayload(api.initial());
    gameOver = Boolean(payload.game_over);
    renderPayload(payload);
    initialized = true;

    if (gameOver) {
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
    renderPayload(payload);
    if (gameOver) {
      setStatus("Game over. Start a new game to continue.", true);
    } else {
      setStatus("Enter a command to continue.");
    }
  }

  async function handleReset() {
    const payload = parsePayload(api.reset());
    gameOver = Boolean(payload.game_over);
    renderPayload(payload);
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

  setInputEnabled(false);
  startGame().catch((error) => {
    setStatus("Startup failed. Check console for details.", true);
    terminal.textContent = String(error);
    renderActions("Available actions", [], false);
    actionsEmpty.textContent = "Unable to load actions.";
    console.error(error);
  });
})();
