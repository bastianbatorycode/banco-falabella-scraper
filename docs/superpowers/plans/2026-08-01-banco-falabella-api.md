# Banco Falabella API Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Expose Banco Falabella read-only scraping as an English Flask API with endpoints for periods, movements, and current available balance.

**Architecture:** Keep Selenium in one reusable scraper module that owns browser setup, login, period discovery, movement collection, and balance extraction. Put the HTTP layer in Flask and have it serialize Python data structures directly, without a second JSON parsing step. Each request runs a fresh browser session with no persisted cookies or profile state.

**Tech Stack:** Python, Flask, Selenium, pytest, monkeypatching for route isolation, headless Chrome.

## Global Constraints

- API routes, request fields, and response fields must be in English.
- Credentials are passed as request parameters/body fields, never stored on disk.
- Each API request uses one isolated Selenium session and tears it down after the response.
- Do not persist cookies, browser profiles, screenshots, or downloaded bank files in the repository.
- The API layer must return Python objects directly; it must not perform an extra JSON parsing step.
- The service should work in headless mode on Raspberry Pi without requiring a GUI.

---

### Task 1: Extract the Selenium service core

**Files:**
- Create: `bank_falabella_service.py`
- Modify: `prototype.py`

**Interfaces:**
- Consumes: Selenium driver creation, login flow, banner dismissal, period select, export/download, XLS-to-rows conversion.
- Produces:
  - `create_driver(headless: bool) -> tuple[webdriver.Chrome, Path, Path]`
  - `login_and_open_account(driver, rut: str, password: str) -> None`
  - `list_periods(driver) -> list[str]`
  - `collect_movements_for_period(driver, download_dir: Path, period_label: str) -> list[dict[str, object]]`
  - `collect_movements_for_range(rut: str, password: str, period_start: str, period_end: str, headless: bool = True) -> list[dict[str, object]]`
  - `get_available_balance(rut: str, password: str, headless: bool = True) -> int`

- [ ] **Step 1: Write the failing test**

```python
def test_collect_movements_for_range_uses_one_session(monkeypatch):
    calls = []

    class FakeService:
        def collect(self, period):
            calls.append(period)
            return [{"period": period}]

    result = collect_movements_for_range("17944027-K", "314159", "04-2026", "06-2026")

    assert result == [
        {"period": "06-2026"},
        {"period": "05-2026"},
        {"period": "04-2026"},
    ]
    assert calls == ["06-2026", "05-2026", "04-2026"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_service.py::test_collect_movements_for_range_uses_one_session -v`
Expected: FAIL because the service module and range collector do not exist yet.

- [ ] **Step 3: Write minimal implementation**

```python
def collect_movements_for_range(rut: str, password: str, period_start: str, period_end: str, headless: bool = True):
    periods = expand_period_range(period_start, period_end)
    driver, download_dir, profile_dir = create_driver(headless=headless)
    try:
        login_and_open_account(driver, rut, password)
        rows = []
        for period in periods:
            rows.extend(collect_movements_for_period(driver, download_dir, period))
        return rows
    finally:
        driver.quit()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_service.py::test_collect_movements_for_range_uses_one_session -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add bank_falabella_service.py prototype.py tests/test_service.py
git commit -m "feat: extract falabella scraper service"
```

### Task 2: Add the Flask API layer

**Files:**
- Create: `app.py`
- Create: `tests/test_api.py`
- Modify: `README.md`

**Interfaces:**
- Consumes: the service functions from `bank_falabella_service.py`.
- Produces:
  - `POST /periods`
  - `POST /movements`
  - `POST /balance`

- [ ] **Step 1: Write the failing test**

```python
def test_periods_endpoint_returns_english_payload(monkeypatch, client):
    monkeypatch.setattr("app.list_periods_for_credentials", lambda rut, password, headless=True: ["07-2026", "06-2026"])

    response = client.post("/periods", json={"rut": "17944027-K", "password": "314159"})

    assert response.status_code == 200
    assert response.get_json() == {"periods": ["07-2026", "06-2026"]}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_api.py::test_periods_endpoint_returns_english_payload -v`
Expected: FAIL because the Flask app and route do not exist yet.

- [ ] **Step 3: Write minimal implementation**

```python
from flask import Flask, jsonify, request

app = Flask(__name__)

@app.post("/periods")
def periods():
    payload = request.get_json(force=True)
    periods = list_periods_for_credentials(payload["rut"], payload["password"])
    return jsonify({"periods": periods})
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_api.py::test_periods_endpoint_returns_english_payload -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add app.py tests/test_api.py README.md
git commit -m "feat: add falabella flask api"
```

### Task 3: Add balance extraction and range behavior

**Files:**
- Modify: `bank_falabella_service.py`
- Modify: `app.py`
- Modify: `tests/test_service.py`
- Modify: `tests/test_api.py`

**Interfaces:**
- Consumes: browser session helpers and balance locator.
- Produces:
  - `get_available_balance(...) -> int`
  - `POST /balance`
  - `POST /movements` with `period_start` and `period_end`

- [ ] **Step 1: Write the failing test**

```python
def test_balance_endpoint_returns_integer(monkeypatch, client):
    monkeypatch.setattr("app.get_balance_for_credentials", lambda rut, password, headless=True: 2721)

    response = client.post("/balance", json={"rut": "17944027-K", "password": "314159"})

    assert response.status_code == 200
    assert response.get_json() == {"available_balance": 2721}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_api.py::test_balance_endpoint_returns_integer -v`
Expected: FAIL because the balance route does not exist yet.

- [ ] **Step 3: Write minimal implementation**

```python
@app.post("/balance")
def balance():
    payload = request.get_json(force=True)
    amount = get_balance_for_credentials(payload["rut"], payload["password"])
    return jsonify({"available_balance": amount})
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_api.py::test_balance_endpoint_returns_integer -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add app.py bank_falabella_service.py tests/test_api.py tests/test_service.py
git commit -m "feat: add balance and range scraping"
```

### Task 4: Update docs and Raspberry Pi notes

**Files:**
- Modify: `README.md`
- Create: `requirements.txt`

**Interfaces:**
- Consumes: final Flask API and service contract.
- Produces: installation/run instructions in English payload examples and Raspberry Pi notes.

- [ ] **Step 1: Write the failing test**

```python
def test_readme_mentions_headless_and_raspberry_pi():
    text = Path("README.md").read_text(encoding="utf-8")
    assert "Flask" in text
    assert "Raspberry Pi" in text
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_docs.py::test_readme_mentions_headless_and_raspberry_pi -v`
Expected: FAIL until the docs mention the new API and deployment constraints.

- [ ] **Step 3: Write minimal implementation**

```text
Document:
- API routes in English
- payload examples in English
- headless-only browser requirement
- Raspberry Pi runtime expectations
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_docs.py::test_readme_mentions_headless_and_raspberry_pi -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add README.md requirements.txt
git commit -m "docs: describe falabella api and pi runtime"
```
