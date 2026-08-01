from __future__ import annotations

from pathlib import Path

from flask import Flask, jsonify, request

from bank_falabella_service import (
    collect_movements_for_range,
    get_available_balance,
    list_periods_for_credentials,
    parse_test_spreadsheets,
)


app = Flask(__name__)
TESTDATA_DIR = Path(__file__).resolve().parent / "testdata"


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
            _required_field(payload, "username"),
            _required_field(payload, "password"),
        )
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    return jsonify({"periods": periods})


@app.post("/movements")
def movements():
    payload = _json_payload()
    try:
        rows = _collect_movements_for_request(
            _required_field(payload, "username"),
            _required_field(payload, "password"),
            _required_field(payload, "period_start"),
            _required_field(payload, "period_end"),
        )
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
            _required_field(payload, "username"),
            _required_field(payload, "password"),
        )
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    return jsonify({"available_balance": amount})


@app.post("/parse-test")
def parse_test():
    payload = _json_payload()
    file_names = payload.get("files")
    if file_names is None:
        paths = sorted(
            [
                path
                for path in TESTDATA_DIR.iterdir()
                if path.is_file() and path.suffix.lower() in {".xls", ".xlsx"}
            ]
        )
    else:
        if not isinstance(file_names, list):
            return jsonify({"error": "files must be a list of filenames"}), 400
        paths = [TESTDATA_DIR / str(name) for name in file_names]

    if len(paths) < 2:
        return jsonify({"error": "At least two test spreadsheets are required"}), 400

    missing = [str(path.name) for path in paths if not path.exists()]
    if missing:
        return jsonify({"error": "Missing test spreadsheets", "missing": missing}), 400

    parsed = parse_test_spreadsheets(paths)
    movements = []
    for item in parsed:
        movements.extend(item["movements"])
    return jsonify(
        {
            "files": [item["file"] for item in parsed],
            "file_count": len(parsed),
            "movement_count": len(movements),
            "movements": movements,
        }
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
