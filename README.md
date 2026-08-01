# Banco Falabella API

Read-only Flask API for Banco Falabella Cuenta Corriente.

It exposes three endpoints:

- `POST /periods`
- `POST /movements`
- `POST /balance`

## Input

Send JSON with:

- `username`
- `password`
- `period_start` and `period_end` for `/movements`

## Output

The API returns English JSON keys:

- `periods`
- `period_start`
- `period_end`
- `movements`
- `available_balance`

Money values are returned as integers.
Periods are returned as `MM-YYYY`.

## Run

```powershell
python -m pip install -r requirements.txt
python .\app.py
```

The service starts on `0.0.0.0:5000`.

## Notes

- Each request opens a fresh browser session.
- No credentials, cookies, screenshots, or spreadsheet files are stored in the repo.
- Selenium runs headless when the underlying browser session is configured that way.
- The API does not expose GUI automation or banking actions beyond read-only scraping.
