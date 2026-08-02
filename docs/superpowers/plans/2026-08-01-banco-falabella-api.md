# Banco Falabella API Archive

> Historical note: this initial API plan was completed and then superseded by the module rename and POM refactor archive.

## Final outcome

- Read-only Flask API for Banco Falabella Cuenta Corriente
- English request and response payloads
- Current endpoints:
  - `POST /periods`
  - `POST /movements`
  - `POST /balance`
- Credentials can be provided by request JSON or local `.env`
- `/periods` returns the valid `MM-YYYY` values used by `/movements`

## Current implementation files

- `falabella_api.py`
- `falabella_service.py`
- `falabella_browser.py`
- `falabella_pages/`

## Verification

- `./.venv/bin/python -m pytest -q`
- Result: `15 passed`

## Historical note

- `POST /parse-test` was removed intentionally and should not be reintroduced
