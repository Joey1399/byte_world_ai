"""Web host for byte_world_ai using a browser terminal emulator."""

from __future__ import annotations

from dataclasses import dataclass
import html
import os
import re
from threading import Lock
from uuid import uuid4

from flask import Flask, jsonify, render_template, request, session

# Force ANSI color rendering before importing the game UI module.
os.environ.setdefault("BYTE_WORLD_AI_FORCE_COLOR", "1")
os.environ.setdefault("BYTE_WORLD_AI_NO_CLEAR", "1")

from game.engine import Engine
from game.state import GameState, create_initial_state


SESSION_KEY = "byte_world_ai_session_id"
ANSI_COLOR_CLASSES = {
    "38;5;39": "ansi-blue",
    "93": "ansi-yellow",
    "38;5;208": "ansi-orange",
    "91": "ansi-red",
    "92": "ansi-green",
    "95": "ansi-purple",
    "38;5;213": "ansi-pink",
}
ANSI_RE = re.compile(r"\x1b\[([0-9;]+)m")
CONTROL_RE = re.compile(r"\x1b\[(?![0-9;]*m)[0-9;]*[A-Za-z]")


@dataclass
class BrowserGame:
    state: GameState
    screen: str


app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "byte_world_ai_dev_secret")
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

_ENGINE = Engine()
_SESSIONS: dict[str, BrowserGame] = {}
_SESSIONS_LOCK = Lock()


def _ansi_to_html(text: str) -> str:
    if not text:
        return ""

    clean = CONTROL_RE.sub("", text).replace("\r", "")
    parts: list[str] = []
    cursor = 0
    span_open = False

    for match in ANSI_RE.finditer(clean):
        segment = clean[cursor : match.start()]
        if segment:
            parts.append(html.escape(segment))

        code = match.group(1)
        if code == "0":
            if span_open:
                parts.append("</span>")
                span_open = False
        else:
            css_class = ANSI_COLOR_CLASSES.get(code)
            if css_class:
                if span_open:
                    parts.append("</span>")
                parts.append(f'<span class="{css_class}">')
                span_open = True

        cursor = match.end()

    trailing = clean[cursor:]
    if trailing:
        parts.append(html.escape(trailing))

    if span_open:
        parts.append("</span>")

    return "".join(parts)


def _new_browser_game() -> BrowserGame:
    state = create_initial_state()
    screen = _ENGINE.initial_screen(state)
    return BrowserGame(state=state, screen=screen)


def _session_id() -> str:
    session_id = session.get(SESSION_KEY)
    if isinstance(session_id, str) and session_id:
        return session_id
    session_id = uuid4().hex
    session[SESSION_KEY] = session_id
    return session_id


def _get_browser_game() -> BrowserGame:
    session_id = _session_id()
    with _SESSIONS_LOCK:
        game = _SESSIONS.get(session_id)
        if game is None:
            game = _new_browser_game()
            _SESSIONS[session_id] = game
        return game


@app.get("/")
def index() -> str:
    game = _get_browser_game()
    return render_template(
        "index.html",
        screen_html=_ansi_to_html(game.screen),
        game_over=game.state.game_over,
    )


@app.post("/command")
def command() -> tuple[object, int] | object:
    payload = request.get_json(silent=True) or {}
    raw_command = str(payload.get("command", "")).strip()
    game = _get_browser_game()

    if raw_command and not game.state.game_over:
        game.screen = _ENGINE.process_raw_command(game.state, raw_command)

    return jsonify(
        {
            "screen_html": _ansi_to_html(game.screen),
            "game_over": game.state.game_over,
        }
    )


@app.post("/reset")
def reset() -> object:
    session_id = _session_id()
    with _SESSIONS_LOCK:
        _SESSIONS[session_id] = _new_browser_game()
        game = _SESSIONS[session_id]

    return jsonify(
        {
            "screen_html": _ansi_to_html(game.screen),
            "game_over": game.state.game_over,
        }
    )


@app.get("/health")
def health() -> object:
    return {"status": "ok"}


if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    app.run(host="0.0.0.0", port=port)
