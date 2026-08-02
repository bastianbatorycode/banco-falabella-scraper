# Banco Falabella Agent Guide

This repository is the read-only Banco Falabella Flask API.

Current stable branch:
- `v1-functional-base`

Current stable endpoints:
- `POST /periods`
- `POST /movements`
- `POST /balance`

Removed on purpose:
- `POST /parse-test`

Rules for future Codex runs:
- Work from the repository root: `/home/basti/banco-falabella`
- Keep the flow read-only; do not persist bank data, screenshots, or credentials
- Prefer `.venv/bin/python` over system `python`
- Read `README.md` and `docs/CODEX_HANDOFF.md` before changing behavior
- Use `USERNAME` and `PASSWORD` from request JSON or local `.env`
- Keep `parse-test` out of the API, docs, and Postman collection
- The primary modules are `falabella_api.py`, `falabella_service.py`, `falabella_browser.py`, and `falabella_pages/`.
- `/periods` is the source of valid `MM-YYYY` values for `/movements`.

Known-good verification:
- `./.venv/bin/python -m pytest -q`

If Selenium fails in a fresh environment:
- confirm `chromium` and `chromedriver` exist
- confirm the browser flags in `falabella_browser.py`
- treat transport failures as environment issues before changing business logic
