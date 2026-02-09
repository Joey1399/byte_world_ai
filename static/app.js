(() => {
  const terminal = document.getElementById("terminal");
  const form = document.getElementById("command-form");
  const input = document.getElementById("command-input");
  const resetButton = document.getElementById("reset-button");
  const statusLine = document.getElementById("status-line");

  let busy = false;
  let gameOver = Boolean(window.BYTE_WORLD_BOOTSTRAP && window.BYTE_WORLD_BOOTSTRAP.gameOver);

  function setStatus(message, isError = false) {
    statusLine.textContent = message;
    statusLine.classList.toggle("over", isError);
  }

  function applyScreen(screenHtml, isGameOver) {
    terminal.innerHTML = screenHtml;
    terminal.scrollTop = 0;
    gameOver = Boolean(isGameOver);
    if (gameOver) {
      setStatus("Game over. Start a new game to continue.", true);
    } else {
      setStatus("Enter a command to continue.");
    }
  }

  async function postJson(url, body) {
    const response = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    if (!response.ok) {
      throw new Error(`Request failed (${response.status})`);
    }
    return response.json();
  }

  async function postEmpty(url) {
    const response = await fetch(url, { method: "POST" });
    if (!response.ok) {
      throw new Error(`Request failed (${response.status})`);
    }
    return response.json();
  }

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (busy || gameOver) {
      return;
    }

    const command = input.value.trim();
    if (!command) {
      input.focus();
      return;
    }

    busy = true;
    input.disabled = true;
    setStatus("Running command...");

    try {
      const payload = await postJson("/command", { command });
      applyScreen(payload.screen_html, payload.game_over);
      input.value = "";
    } catch (error) {
      setStatus("Unable to reach server. Try again.", true);
    } finally {
      busy = false;
      input.disabled = false;
      input.focus();
    }
  });

  resetButton.addEventListener("click", async () => {
    if (busy) {
      return;
    }

    busy = true;
    input.disabled = true;
    setStatus("Starting new game...");

    try {
      const payload = await postEmpty("/reset");
      applyScreen(payload.screen_html, payload.game_over);
      input.value = "";
    } catch (error) {
      setStatus("Unable to reset game. Try again.", true);
    } finally {
      busy = false;
      input.disabled = false;
      input.focus();
    }
  });

  if (gameOver) {
    setStatus("Game over. Start a new game to continue.", true);
  } else {
    setStatus("Enter a command to continue.");
  }
  input.focus();
})();
