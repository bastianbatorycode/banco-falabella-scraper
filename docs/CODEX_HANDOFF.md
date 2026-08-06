# Codex Handoff

This document is the shortest path for a remote Codex agent to continue work from the current stable version.
Use [AGENTS.md](/home/basti/banco-falabella/AGENTS.md) for operating rules and repo conventions.

## What is stable now

- Branch: `v1-functional-base`
- API routes: `POST /periods`, `POST /movements`, `POST /balance`
- Credentials source: request JSON or local `.env`
- Removed route: `POST /parse-test`
- Primary runtime modules: `falabella_api.py`, `falabella_service.py`, `falabella_browser.py`, and `falabella_pages/`

## Start from here

```bash
cd /home/basti/banco-falabella
source .venv/bin/activate
```

If you want environment-backed credentials:

```bash
printf 'USERNAME=tu_rut\nPASSWORD=tu_password\n' > .env
```

Run the test suite:

```bash
./.venv/bin/python -m pytest -q
```

Run the API:

```bash
./.venv/bin/python falabella_api.py
```

## Quick checks

- `/periods` should return a descending list of `MM-YYYY` values
- `/balance` should return `{"available_balance": <int>}`
- `/movements` should return the requested period range plus parsed rows
- `/periods` is the source for valid `MM-YYYY` inputs for `/movements`

## Useful files

- [README.md](/home/basti/banco-falabella/README.md)
- [AGENTS.md](/home/basti/banco-falabella/AGENTS.md)
- [falabella_api.py](/home/basti/banco-falabella/falabella_api.py)
- [falabella_service.py](/home/basti/banco-falabella/falabella_service.py)
- [falabella_browser.py](/home/basti/banco-falabella/falabella_browser.py)
