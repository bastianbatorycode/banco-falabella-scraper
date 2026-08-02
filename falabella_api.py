from __future__ import annotations

import os
from pathlib import Path

from flask import Flask, jsonify, request

from falabella_service import (
    collect_movements_for_range,
    get_available_balance,
    list_periods_for_credentials,
    TransportError,
)


app = Flask(__name__)
DOTENV_PATH = Path(__file__).resolve().parent / ".env"


def _load_dotenv(path: Path = DOTENV_PATH) -> None:
    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if not key:
            continue
        value = value.strip()
        if value and len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        os.environ.setdefault(key, value)


_load_dotenv()


def _json_payload():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return {}
    return payload


def _required_field(payload, name: str) -> str:
    value = payload.get(name)
    if not value:
        raise ValueError(f"Missing required field: {name}")
    return value


def _required_credential(payload, name: str, env_name: str) -> str:
    value = payload.get(name) or os.environ.get(env_name)
    if not value:
        raise ValueError(f"Missing required field: {name}")
    return value


def _list_periods_for_request(username: str, password: str):
    return list_periods_for_credentials(username, password)


def _collect_movements_for_request(username: str, password: str, period_start: str, period_end: str):
    return collect_movements_for_range(username, password, period_start, period_end)


def _get_available_balance_for_request(username: str, password: str):
    return get_available_balance(username, password)


@app.post("/periods")
def periods():
    payload = _json_payload()
    try:
        periods = _list_periods_for_request(
            _required_credential(payload, "username", "USERNAME"),
            _required_credential(payload, "password", "PASSWORD"),
        )
    except TransportError as exc:
        return jsonify({"error": str(exc)}), 503
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    return jsonify({"periods": periods})


@app.post("/movements")
def movements():
    payload = _json_payload()
    try:
        rows = _collect_movements_for_request(
            _required_credential(payload, "username", "USERNAME"),
            _required_credential(payload, "password", "PASSWORD"),
            _required_field(payload, "period_start"),
            _required_field(payload, "period_end"),
        )
    except TransportError as exc:
        return jsonify({"error": str(exc)}), 503
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    return jsonify(
        {
            "period_start": payload["period_start"],
            "period_end": payload["period_end"],
            "movements": rows,
        }
    )


@app.post("/balance")
def balance():
    payload = _json_payload()
    try:
        amount = _get_available_balance_for_request(
            _required_credential(payload, "username", "USERNAME"),
            _required_credential(payload, "password", "PASSWORD"),
        )
    except TransportError as exc:
        return jsonify({"error": str(exc)}), 503
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    return jsonify({"available_balance": amount})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
