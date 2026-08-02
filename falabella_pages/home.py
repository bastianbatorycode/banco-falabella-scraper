from __future__ import annotations

import re
import time

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from falabella_browser import ACTION_DELAY_SECONDS
from falabella_pages.base import BasePage


class HomePage(BasePage):
    def open_current_account(self) -> None:
        wait = self.wait
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
        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", card)
        self.driver.execute_script("arguments[0].click();", card)
        time.sleep(ACTION_DELAY_SECONDS)

        try:
            wait.until(EC.staleness_of(card))
        except Exception:
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

    def find_available_balance(self) -> int:
        anchors = self.driver.find_elements(By.XPATH, "//span[normalize-space()='Saldo disponible']")
        if not anchors:
            anchors = self.driver.find_elements(
                By.XPATH,
                "//*[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZÁÉÍÓÚÑ', 'abcdefghijklmnopqrstuvwxyzaeiouñ'), 'saldo disponible')]",
            )
        for anchor in anchors:
            sibling_candidates = []
            try:
                sibling_candidates.append(anchor.find_element(By.XPATH, "./preceding-sibling::*[1]"))
            except Exception:
                pass
            try:
                sibling_candidates.append(anchor.find_element(By.XPATH, "./following-sibling::*[1]"))
            except Exception:
                pass
            for sibling in sibling_candidates:
                if "green-text-bold" not in (sibling.get_attribute("class") or ""):
                    continue
                text = " ".join((sibling.text or "").split())
                match = re.search(r"\$?\s*([\d.]+)", text)
                if match:
                    return int(match.group(1).replace(".", ""))
        raise RuntimeError("Available balance element not found")

