"""Read-only Banco Falabella Cuenta Corriente prototype.

This is intentionally a discovery harness, not a production scraper:
- the user performs login and any navigation manually;
- no credentials, OTPs, cookies, page source, screenshots, or downloaded files
  are persisted;
- the script only reports page structure and read-only-looking links.
"""

from __future__ import annotations

import argparse
import json
from numbers import Number
import re
import tempfile
import time
import shutil
import unicodedata
from datetime import date, datetime
from pathlib import Path

import pandas as pd
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait


LOGIN_URL = "https://www.bancofalabella.cl/BancoFalabellaChile/?STP=login"
ACTION_DELAY_SECONDS = 1.5
LATEST_MOVEMENTS_LABEL = "ultimos movimientos"
CURRENT_MONTH_LABEL = "mes en curso"
VISIBLE_WINDOW_SIZE = "1366,720"
HEADLESS_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) HeadlessChrome/150.0.0.0 Safari/537.36"
)


def open_login_panel(driver: webdriver.Chrome) -> None:
    wait = WebDriverWait(driver, 20)
    account_button = wait.until(
        EC.element_to_be_clickable((By.XPATH, '//button[normalize-space()="Mi cuenta"]'))
    )
    account_button.click()
    time.sleep(ACTION_DELAY_SECONDS)


def is_authenticated(driver: webdriver.Chrome) -> bool:
    return "/web-clientes/" in (driver.current_url or "")


def open_current_account(driver: webdriver.Chrome) -> None:
    wait = WebDriverWait(driver, 20)
    cards = wait.until(
        lambda d: [
            element
            for element in d.find_elements(By.CSS_SELECTOR, "a.div-product")
            if element.is_displayed() and "cuenta corriente" in (element.text or "").casefold()
        ]
    )
    if len(cards) != 1:
        raise RuntimeError(f"Expected 1 Cuenta Corriente card and found {len(cards)}.")
    card = cards[0]
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", card)
    driver.execute_script("arguments[0].click();", card)
    time.sleep(ACTION_DELAY_SECONDS)

    try:
        wait.until(EC.staleness_of(card))
    except TimeoutException:
        wait.until(
            lambda d: any(
                element.is_displayed()
                and any(
                    word in (element.text or "").casefold()
                    for word in ("movimiento", "cartola")
                )
                for element in d.find_elements(By.CSS_SELECTOR, "a,button,h1,h2,h3,[role=button]")
            )
        )


def submit_login(driver: webdriver.Chrome, rut: str, password: str) -> None:
    wait = WebDriverWait(driver, 20)
    rut_input = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, 'input[placeholder="RUT"]')))
    password_input = wait.until(
        EC.visibility_of_element_located((By.CSS_SELECTOR, 'input[placeholder="Clave Internet"]'))
    )
    rut_input.clear()
    rut_input.send_keys(rut)
    time.sleep(ACTION_DELAY_SECONDS)
    password_input.clear()
    password_input.send_keys(password)
    time.sleep(ACTION_DELAY_SECONDS)

    submit = None
    candidates = driver.find_elements(By.CSS_SELECTOR, 'button[class*="login-button"]')
    enabled = [button for button in candidates if button.is_displayed() and button.is_enabled()]
    if enabled:
        submit = enabled[0]
    else:
        panel = password_input.find_element(By.XPATH, "ancestor::*[.//button][1]")
        buttons = panel.find_elements(By.CSS_SELECTOR, 'button[type="submit"], button')
        enabled = [button for button in buttons if button.is_displayed() and button.is_enabled()]
        if enabled:
            submit = enabled[0]
    if submit is None:
        raise RuntimeError("No enabled login button was found.")
    submit.click()
    time.sleep(ACTION_DELAY_SECONDS)


def close_post_login_banner(driver: webdriver.Chrome) -> None:
    wait = WebDriverWait(driver, 5)
    try:
        button = wait.until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="shadow-container"]/button'))
        )
    except TimeoutException:
        return
    if not button.is_displayed():
        return
    try:
        button.click()
    except WebDriverException:
        driver.execute_script("arguments[0].click();", button)
    time.sleep(ACTION_DELAY_SECONDS)


def gather_browser_fingerprint(driver: webdriver.Chrome) -> dict[str, object]:
    return {
        "url": driver.current_url,
        "title": driver.title,
        "user_agent": driver.execute_script("return navigator.userAgent"),
        "webdriver": driver.execute_script("return navigator.webdriver"),
        "language": driver.execute_script("return navigator.language"),
        "languages": driver.execute_script("return navigator.languages"),
        "plugins": driver.execute_script("return navigator.plugins.length"),
        "screen": driver.execute_script(
            "return [window.outerWidth, window.outerHeight, window.innerWidth, window.innerHeight]"
        ),
        "timezone": driver.execute_script(
            "return Intl.DateTimeFormat().resolvedOptions().timeZone"
        ),
    }


def print_fingerprint(driver: webdriver.Chrome, stage: str) -> None:
    print(json.dumps({"fingerprint_stage": stage, **gather_browser_fingerprint(driver)}, ensure_ascii=False, indent=2))


def apply_browser_spoofs(
    driver: webdriver.Chrome,
    *,
    spoof_headless_ua: bool,
    spoof_headless_window: bool,
) -> None:
    if spoof_headless_window:
        driver.set_window_size(1920, 1080)
    if spoof_headless_ua:
        driver.execute_cdp_cmd(
            "Network.setUserAgentOverride",
            {
                "userAgent": HEADLESS_USER_AGENT,
                "acceptLanguage": "es-CL,es;q=0.9",
                "platform": "Windows",
            },
        )


def movement_period_select(driver: webdriver.Chrome):
    visible_selects = [
        element for element in driver.find_elements(By.CSS_SELECTOR, "select") if element.is_displayed()
    ]
    if not visible_selects:
        raise RuntimeError("No visible period selector was found.")

    def select_score(element) -> tuple[int, list[str]]:
        option_labels = [" ".join(option.text.split()) for option in Select(element).options]
        folded_labels = {ascii_fold(label).casefold() for label in option_labels if label}
        score = 0
        if CURRENT_MONTH_LABEL in folded_labels:
            score += 5
        if LATEST_MOVEMENTS_LABEL in folded_labels:
            score += 3
        if any(re.fullmatch(r"\d{2}/\d{4}", label) for label in option_labels):
            score += 2
        if any(re.fullmatch(r"\d{2}-\d{4}", label) for label in option_labels):
            score += 2
        if len(option_labels) >= 3:
            score += 1
        return score, option_labels

    scored = [(select_score(element), element) for element in visible_selects]
    scored.sort(key=lambda item: item[0][0], reverse=True)
    best_score, best_options = scored[0][0]
    if best_score <= 0:
        raise RuntimeError(
            f"No period selector matched the expected options; found {len(visible_selects)} visible select(s) "
            f"with labels: {best_options}"
        )
    return scored[0][1]


def ascii_fold(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    return "".join(char for char in normalized if not unicodedata.combining(char))


def get_movement_periods(driver: webdriver.Chrome) -> list[dict[str, str]]:
    select = Select(movement_period_select(driver))
    periods = []
    for option in select.options:
        label = " ".join(option.text.split())
        folded_label = ascii_fold(label).casefold()
        if label and folded_label != LATEST_MOVEMENTS_LABEL:
            periods.append({"label": label, "value": option.get_attribute("value") or label})
    if not any(ascii_fold(item["label"]).casefold() == CURRENT_MONTH_LABEL for item in periods):
        raise RuntimeError("The selector does not offer 'Mes en curso'.")
    return periods


def select_movement_period(driver: webdriver.Chrome, label: str) -> None:
    select_element = movement_period_select(driver)
    select = Select(select_element)
    labels = [" ".join(option.text.split()) for option in select.options]
    if label not in labels or ascii_fold(label).casefold() == LATEST_MOVEMENTS_LABEL:
        raise ValueError("Invalid or disallowed period.")
    value = next(
        option.get_attribute("value") or option.text
        for option in select.options
        if " ".join(option.text.split()) == label
    )
    driver.execute_script(
        """
        const select = arguments[0];
        const value = arguments[1];
        select.value = value;
        select.dispatchEvent(new Event('input', {bubbles: true}));
        select.dispatchEvent(new Event('change', {bubbles: true}));
        """,
        select_element,
        value,
    )
    time.sleep(ACTION_DELAY_SECONDS)


def choose_period_from_terminal(periods: list[dict[str, str]]) -> str:
    print("Periodos disponibles para consultar:")
    for index, period in enumerate(periods, start=1):
        print(f"{index}. {period['label']}")
    while True:
        answer = input("Selecciona el numero del periodo: ").strip()
        try:
            return periods[int(answer) - 1]["label"]
        except (ValueError, IndexError):
            print("Opcion invalida. Escribe uno de los numeros mostrados.")


def click_export_excel(driver: webdriver.Chrome) -> None:
    candidates = []
    for element in driver.find_elements(By.CSS_SELECTOR, "button,a,[role='button'],img"):
        if not element.is_displayed():
            continue
        text = " ".join(
            (
                element.text or "",
                element.get_attribute("aria-label") or "",
                element.get_attribute("title") or "",
                element.get_attribute("alt") or "",
            )
        ).casefold()
        if "excel" not in text and "exportar" not in text:
            continue
        clickable = element
        if element.tag_name.lower() == "img":
            clickable = element.find_element(
                By.XPATH, "ancestor::*[self::button or self::a or @role='button'][1]"
            )
        if clickable not in candidates:
            candidates.append(clickable)
    if len(candidates) != 1:
        raise RuntimeError(f"Expected 1 'Exportar a Excel' control and found {len(candidates)}.")
    driver.execute_script("arguments[0].click();", candidates[0])


def wait_for_spreadsheet(download_dir: Path, timeout_seconds: int = 45) -> Path:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        files = [
            path
            for pattern in ("*.xlsx", "*.xls")
            for path in download_dir.glob(pattern)
            if not path.name.endswith(".crdownload")
        ]
        if files:
            return max(files, key=lambda path: path.stat().st_mtime)
        time.sleep(0.5)
    raise TimeoutException("No spreadsheet download appeared within the expected time.")


def normalize_period_label(value: str) -> str:
    return value.replace("/", "-")


def parse_money(value: object) -> int | None:
    if value is None:
        return None
    if isinstance(value, float) and value != value:
        return None
    if isinstance(value, Number) and not isinstance(value, bool):
        return int(value)
    text = " ".join(str(value).split())
    if not text:
        return None
    if re.fullmatch(r"\d{1,2}-\d{1,2}-\d{4}", text):
        return None
    digits = re.sub(r"[^\d-]", "", text)
    if not digits or digits == "-":
        return None
    return int(digits)


def json_cell(value: object) -> object:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if value is None:
        return None
    if isinstance(value, float) and value != value:
        return None
    if isinstance(value, str) and not value.strip():
        return None
    return " ".join(str(value).split())


def json_money_cell(value: object) -> int | None:
    return parse_money(value)


def rows_to_json(rows: list[list[str]]) -> list[dict[str, object]]:
    if not rows:
        return []

    expected_headers = {"fecha", "descripcion", "cargo", "abono", "saldo"}
    header_index = None
    keys: list[str] | None = None
    max_header_scan = min(len(rows), 12)

    for candidate_index in range(max_header_scan):
        candidate = rows[candidate_index]
        normalized = [ascii_fold(" ".join(str(value or "").split())).casefold() for value in candidate]
        match_count = sum(1 for value in normalized if value in expected_headers)
        if match_count >= 3:
            header_index = candidate_index
            keys = [
                {
                    "fecha": "fecha",
                    "descripcion": "descripcion",
                    "cargo": "cargo",
                    "abono": "abono",
                    "saldo": "saldo",
                }.get(header, header or f"columna_{index}")
                for index, header in enumerate(normalized)
            ]
            break

    if header_index is None or keys is None:
        return []

    records: list[dict[str, object]] = []
    for row in rows[header_index + 1 :]:
        if not any(value is not None and str(value).strip() for value in row):
            continue
        record: dict[str, object] = {}
        for index, value in enumerate(row):
            if index >= len(keys):
                continue
            key = keys[index]
            if key in {"cargo", "abono", "saldo"}:
                record[key] = json_money_cell(value)
            elif key == "fecha":
                record[key] = json_cell(value)
            else:
                record[key] = json_cell(value)
        records.append(record)
    return records


def xlsx_to_json(xlsx_path: Path) -> list[dict[str, object]]:
    engine = "xlrd" if xlsx_path.suffix.lower() == ".xls" else "openpyxl"
    sheets = pd.read_excel(xlsx_path, sheet_name=None, header=None, engine=engine)
    best_rows: list[dict[str, object]] = []
    for frame in sheets.values():
        rows = frame.where(pd.notna(frame), None).values.tolist()
        parsed_rows = rows_to_json(rows)
        if len(parsed_rows) > len(best_rows):
            best_rows = parsed_rows
    return best_rows


def build_report(period_label: str, xlsx_path: Path) -> dict[str, object]:
    return {
        "periodo": normalize_period_label(period_label),
        "movimientos": xlsx_to_json(xlsx_path),
    }


def create_driver(headless: bool) -> tuple[webdriver.Chrome, Path, Path]:
    options = Options()
    options.add_argument("--lang=es-CL")
    if headless:
        options.add_argument("--headless")
        options.add_argument("--window-size=1366,720")
        options.add_argument("--disable-gpu")
        options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36')
    else:
        options.add_argument("--start-maximized")

    download_dir = Path(tempfile.mkdtemp(prefix="banco-falabella-downloads-"))
    profile_dir = Path(tempfile.mkdtemp(prefix="banco-falabella-profile-"))
    options.add_experimental_option(
        "prefs",
        {
            "download.default_directory": str(download_dir),
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True,
        },
    )
    options.add_argument(f"--user-data-dir={profile_dir}")
    driver = webdriver.Chrome(options=options)
    driver.execute_cdp_cmd(
        "Page.setDownloadBehavior",
        {
            "behavior": "allow",
            "downloadPath": str(download_dir),
        },
    )
    return driver, download_dir, profile_dir


def export_selected_period_report(
    driver: webdriver.Chrome,
    download_dir: Path,
    selected_period: str,
) -> dict[str, object]:
    select_movement_period(driver, selected_period)
    click_export_excel(driver)
    xlsx_path = wait_for_spreadsheet(download_dir)
    return build_report(selected_period, xlsx_path)


def run_session(
    headless: bool,
    rut: str,
    password: str,
    *,
    diagnose_browser: bool,
    spoof_headless_ua: bool,
    spoof_headless_window: bool,
) -> dict[str, object]:
    driver, download_dir, profile_dir = create_driver(headless=headless)
    try:
        apply_browser_spoofs(
            driver,
            spoof_headless_ua=spoof_headless_ua,
            spoof_headless_window=spoof_headless_window,
        )
        driver.get(LOGIN_URL)
        time.sleep(ACTION_DELAY_SECONDS)
        if diagnose_browser:
            print_fingerprint(driver, "before_login")
        if not is_authenticated(driver):
            open_login_panel(driver)
            submit_login(driver, rut, password)
            close_post_login_banner(driver)
        if diagnose_browser:
            print_fingerprint(driver, "after_login")
        try:
            WebDriverWait(driver, 20).until(lambda d: is_authenticated(d))
            print("SESION_AUTENTICADA: se reutilizo o se obtuvo una sesion valida.")
        except TimeoutException:
            print("LOGIN_INCIERTO: no se confirmo una sesion privada.")
            if diagnose_browser:
                debug_dir = Path(tempfile.mkdtemp(prefix="banco-falabella-diagnose-"))
                screenshot_path = debug_dir / "after-login.png"
                html_path = debug_dir / "after-login.html"
                driver.save_screenshot(str(screenshot_path))
                html_path.write_text(driver.page_source, encoding="utf-8", errors="replace")
                print(f"DEBUG_SCREENSHOT: {screenshot_path}")
                print(f"DEBUG_HTML: {html_path}")
        print(f"RUTA_ACTUAL: {driver.current_url}")
        time.sleep(ACTION_DELAY_SECONDS)
        open_current_account(driver)
        periods = get_movement_periods(driver)
        selected_period = choose_period_from_terminal(periods)
        print(f"Periodo seleccionado: {selected_period}")
        report = export_selected_period_report(driver, download_dir, selected_period)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return report
    except WebDriverException as exc:
        print(f"Error de Selenium/WebDriver: {exc.__class__.__name__}: {exc}")
        raise
    finally:
        driver.quit()
        try:
            shutil.rmtree(download_dir, ignore_errors=True)
        except OSError:
            pass
        shutil.rmtree(profile_dir, ignore_errors=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Banco Falabella read-only movements prototype")
    parser.add_argument("--headless", action="store_true", help="Run Chrome headless")
    parser.add_argument("--rut", required=True, help="RUT for login")
    parser.add_argument("--password", required=True, help="Internet password for login")
    parser.add_argument("--diagnose-browser", action="store_true", help="Print browser fingerprint before and after login")
    parser.add_argument("--spoof-headless-ua", action="store_true", help="Use a headless-like user agent in visible mode")
    parser.add_argument("--spoof-headless-window", action="store_true", help="Use a headless-like window size in visible mode")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    run_session(
        headless=args.headless,
        rut=args.rut,
        password=args.password,
        diagnose_browser=args.diagnose_browser,
        spoof_headless_ua=args.spoof_headless_ua,
        spoof_headless_window=args.spoof_headless_window,
    )


if __name__ == "__main__":
    main()
