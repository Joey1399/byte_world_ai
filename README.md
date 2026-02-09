# byte_world_ai

`byte_world_ai` is a terminal-style RPG that can run locally as a CLI or as a browser-hosted CLI emulator.

## Local CLI

```bash
python main.py
```

## Local web mode

```bash
python -m venv .venv
. .venv/Scripts/activate  # Windows PowerShell: .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python web_app.py
```

Open `http://localhost:5000`.

## Heroku deploy

This repository includes:
- `Procfile` (`web: gunicorn web_app:app`)
- `requirements.txt`
- `runtime.txt`

Deploy steps:

```bash
heroku login
heroku create <your-app-name>
heroku config:set SECRET_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(48))")
git push heroku main
heroku open
```

If the app already exists:

```bash
heroku git:remote -a <your-app-name>
git push heroku main
```
