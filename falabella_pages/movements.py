from __future__ import annotations

import re
import time
from pathlib import Path

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select

from falabella_browser import (
    ACTION_DELAY_SECONDS,
    CURRENT_MONTH_LABEL,
    LATEST_MOVEMENTS_LABEL,
    ascii_fold,
)
from falabella_pages.base import BasePage


class MovementsPage(BasePage):
    def movement_period_select(self):
        visible_selects = [
            element for element in self.driver.find_elements(By.CSS_SELECTOR, "select") if element.is_displayed()
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

    def get_movement_periods(self) -> list[dict[str, str]]:
        select = Select(self.movement_period_select())
        periods = []
        for option in select.options:
            label = " ".join(option.text.split())
            folded_label = ascii_fold(label).casefold()
            if label and folded_label != LATEST_MOVEMENTS_LABEL:
                periods.append({"label": label, "value": option.get_attribute("value") or label})
        if not any(ascii_fold(item["label"]).casefold() == CURRENT_MONTH_LABEL for item in periods):
            raise RuntimeError("The selector does not offer 'Mes en curso'.")
        return periods

    def select_movement_period(self, label: str) -> None:
        select_element = self.movement_period_select()
        select = Select(select_element)
        labels = [" ".join(option.text.split()) for option in select.options]
        if label not in labels or ascii_fold(label).casefold() == LATEST_MOVEMENTS_LABEL:
            raise ValueError("Invalid or disallowed period.")
        value = next(
            option.get_attribute("value") or option.text
            for option in select.options
            if " ".join(option.text.split()) == label
        )
        self.driver.execute_script(
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

    def click_export_excel(self) -> None:
        candidates = []
        for element in self.driver.find_elements(By.CSS_SELECTOR, "button,a,[role='button'],img"):
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
        self.driver.execute_script("arguments[0].click();", candidates[0])

    def wait_for_spreadsheet(self, download_dir: Path, timeout_seconds: int = 45) -> Path:
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
