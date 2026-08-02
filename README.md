# Banco Falabella API

Read-only Flask API for Banco Falabella Cuenta Corriente.

It exposes three endpoints:

- `POST /periods`
- `POST /movements`
- `POST /balance`

## Input

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
Use `/periods` first to discover valid `MM-YYYY` values for `/movements`.

## Run

```powershell
python -m pip install -r requirements.txt
python .\falabella_api.py
```

The service starts on `0.0.0.0:5000`.

## Credentials

The API can read credentials from request JSON or from local environment variables:

- `USERNAME`
- `PASSWORD`

You can place them in a local `.env` file next to `falabella_api.py`. The file is ignored by git.
