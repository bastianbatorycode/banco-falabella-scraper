# Falabella Module Rename and POM Refactor Archive

> Historical note: this plan has already been executed. The repository now uses the descriptive runtime modules and the Selenium page-object layout.

## Current result

- Runtime modules:
  - `falabella_api.py`
  - `falabella_service.py`
  - `falabella_browser.py`
- Selenium page objects:
  - `falabella_pages/base.py`
  - `falabella_pages/login.py`
  - `falabella_pages/home.py`
  - `falabella_pages/movements.py`
- API routes:
  - `POST /periods`
  - `POST /movements`
  - `POST /balance`
- `/periods` is the source of valid `MM-YYYY` values for `/movements`
- Legacy compatibility shims were removed

## Verification

- `./.venv/bin/python -m pytest -q`
- Result: `15 passed`

## Notes for future changes

- Keep the API, payload keys, and responses in English
- Keep the scraping flow read-only
- Do not reintroduce `POST /parse-test`
- Preserve the current module names unless a new migration is explicitly planned
