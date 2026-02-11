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

  function setInputEnabled(enabled) {
    const value = Boolean(enabled);
    input.disabled = !value;
    sendButton.disabled = !value;
    resetButton.disabled = !value;
    if (value) {
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

    const rows = Array.isArray(actions) ? actions : [];
    if (!rows.length) {
      actionsEmpty.hidden = false;
      actionsEmpty.textContent = isGameOver
        ? "No actions available. Start a new game."
        : "No actions available right now.";
      return;
    }

    const fragment = document.createDocumentFragment();
    for (const row of rows) {
      const command = String(row?.command || "").trim();
      const description = String(row?.description || "").trim();

      const item = document.createElement("li");
      item.className = "actions-item";

      const commandNode = document.createElement("code");
      commandNode.className = "action-command";
      commandNode.textContent = command || "(unknown)";

      const descriptionNode = document.createElement("p");
      descriptionNode.className = "action-description";
      descriptionNode.textContent = description || "No description.";

      item.append(commandNode, descriptionNode);
      fragment.appendChild(item);
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

from game.engine import Engine
from game import ui
from game.state import create_initial_state

_engine = Engine()
_state = create_initial_state()

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
        actions.append(
            {
                "command": command.strip(),
                "description": description.strip(),
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

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (!initialized || busy || gameOver) {
      return;
    }

    const command = input.value.trim();
    if (!command) {
      input.focus();
      return;
    }

    busy = true;
    setInputEnabled(false);
    setStatus("Running command...");
    try {
      await handleCommand(command);
      input.value = "";
    } catch (error) {
      setStatus("Command failed. Refresh page to recover.", true);
      console.error(error);
    } finally {
      busy = false;
      setInputEnabled(true);
    }
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
