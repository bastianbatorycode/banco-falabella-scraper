from __future__ import annotations

import re
import shutil
from datetime import date
from pathlib import Path

from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.common.by import By

from falabella_browser import ascii_fold, create_driver, xlsx_to_json
from falabella_pages.home import HomePage
from falabella_pages.login import LoginPage
from falabella_pages.movements import MovementsPage


class TransportError(RuntimeError):
    pass


def expand_period_range(period_start: str, period_end: str) -> list[str]:
    start_month, start_year = parse_period_label(period_start)
    end_month, end_year = parse_period_label(period_end)
    start_index = start_year * 12 + start_month
    end_index = end_year * 12 + end_month
    if start_index > end_index:
        raise ValueError("period_start must be earlier than or equal to period_end")

    periods: list[str] = []
    for index in range(end_index, start_index - 1, -1):
        year, month = divmod(index, 12)
        if month == 0:
            year -= 1
            month = 12
        periods.append(f"{month:02d}-{year}")
    return periods


def parse_period_label(value: str) -> tuple[int, int]:
    match = re.fullmatch(r"(\d{2})-(\d{4})", value.strip())
    if not match:
        raise ValueError(f"Invalid period label: {value}")
    month = int(match.group(1))
    year = int(match.group(2))
    if month < 1 or month > 12:
        raise ValueError(f"Invalid period label: {value}")
    return month, year


def to_bank_period_label(value: str) -> str:
    if value == date.today().strftime("%m-%Y"):
        return "Mes en curso"
    return value.replace("-", "/")


def normalize_bank_period_label(value: str) -> str:
    return value.replace("/", "-")


def normalize_period_choice_label(value: str) -> str:
    if ascii_fold(value).casefold() == ascii_fold("Mes en curso").casefold():
        return date.today().strftime("%m-%Y")
    return normalize_bank_period_label(value)


def create_session(headless: bool = True):
    try:
        return create_driver(headless=headless)
    except (PermissionError, OSError, RuntimeError, WebDriverException) as exc:
        raise TransportError(f"Unable to start browser session: {exc}") from exc


def login_and_open_account(driver, username: str, password: str) -> None:
    login_page = LoginPage(driver)
    home_page = HomePage(driver)
    login_page.open()
    if not login_page.is_authenticated():
        login_page.open_account_menu()
        login_page.submit_login(username, password)
        login_page.close_post_login_banner()
    try:
        login_page.wait.until(lambda d: login_page.is_authenticated())
    except TimeoutException as exc:
        raise RuntimeError(f"Authentication failed: {driver.current_url}") from exc
    home_page.open_current_account()


def login_and_stay_on_home(driver, username: str, password: str) -> None:
    login_page = LoginPage(driver)
    login_page.open()
    if not login_page.is_authenticated():
        login_page.open_account_menu()
        login_page.submit_login(username, password)
        login_page.close_post_login_banner()
    try:
        login_page.wait.until(lambda d: login_page.is_authenticated())
    except TimeoutException as exc:
        raise RuntimeError(f"Authentication failed: {driver.current_url}") from exc


def list_periods_for_credentials(username: str, password: str, headless: bool = True) -> list[str]:
    driver, download_dir, profile_dir = create_session(headless=headless)
    try:
        login_and_open_account(driver, username, password)
        periods = MovementsPage(driver).get_movement_periods()
        return [normalize_period_choice_label(period["label"]) for period in periods]
    finally:
        driver.quit()
        shutil.rmtree(download_dir, ignore_errors=True)
        shutil.rmtree(profile_dir, ignore_errors=True)


def collect_movements_for_period(driver, download_dir: Path, period_label: str) -> list[dict[str, object]]:
    bank_label = to_bank_period_label(period_label)
    movements_page = MovementsPage(driver)
    movements_page.select_movement_period(bank_label)
    movements_page.click_export_excel()
    xlsx_path = movements_page.wait_for_spreadsheet(download_dir)
    report = read_spreadsheet_rows(xlsx_path)
    try:
        xlsx_path.unlink()
    except OSError:
        pass
    return [
        {
            "period": period_label,
            "date": row.get("date"),
            "description": row.get("description"),
            "debit": row.get("debit"),
            "credit": row.get("credit"),
            "balance": row.get("balance"),
        }
        for row in report
    ]


def collect_movements_for_range(
    username: str,
    password: str,
    period_start: str,
    period_end: str,
    headless: bool = True,
) -> list[dict[str, object]]:
    periods = expand_period_range(period_start, period_end)
    driver, download_dir, profile_dir = create_session(headless=headless)
    try:
        login_and_open_account(driver, username, password)
        rows: list[dict[str, object]] = []
        for period_label in periods:
            rows.extend(collect_movements_for_period(driver, download_dir, period_label))
        return rows
    finally:
        driver.quit()
        shutil.rmtree(download_dir, ignore_errors=True)
        shutil.rmtree(profile_dir, ignore_errors=True)


def find_available_balance(driver) -> int:
    return HomePage(driver).find_available_balance()


def read_spreadsheet_rows(xlsx_path: Path) -> list[dict[str, object]]:
    report = xlsx_to_json(xlsx_path)
    rows: list[dict[str, object]] = []
    for row in report:
        rows.append(
            {
                "date": row.get("fecha"),
                "description": row.get("descripcion"),
                "debit": row.get("cargo"),
                "credit": row.get("abono"),
                "balance": row.get("saldo"),
            }
        )
    return rows


def get_available_balance(username: str, password: str, headless: bool = True) -> int:
    driver, download_dir, profile_dir = create_session(headless=headless)
    try:
        login_and_stay_on_home(driver, username, password)
        home_page = HomePage(driver)
        home_page.wait.until(
            lambda d: d.find_elements(
                By.XPATH,
                "//*[contains(normalize-space(.), 'Saldo disponible')]",
            )
        )
        return home_page.find_available_balance()
    finally:
        driver.quit()
        shutil.rmtree(download_dir, ignore_errors=True)
        shutil.rmtree(profile_dir, ignore_errors=True)
