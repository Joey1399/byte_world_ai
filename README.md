# byte_world_ai

`byte_world_ai` is a terminal-style RPG that runs as:
- a local Python CLI, and
- a public browser version hosted on GitHub Pages.

## Local CLI

```bash
python main.py
```

## Local web preview (GitHub Pages build)

```bash
python -m http.server 8000
```

Open `http://localhost:8000`.

This serves the static site (`index.html`) which runs the Python game engine in-browser via Pyodide.

## GitHub Pages deploy

This repo includes a Pages workflow at `.github/workflows/pages.yml`.

One-time setup in GitHub:
- Repository `Settings` -> `Pages`
- Source: `GitHub Actions`

After that, every push to `main` auto-deploys.

Manual enable with GitHub CLI (optional):

```bash
gh api repos/Joey1399/byte_world_ai/pages -X POST -f build_type=workflow
```

Live URL pattern:

`https://joey1399.github.io/byte_world_ai/`
