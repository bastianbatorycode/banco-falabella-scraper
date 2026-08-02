from __future__ import annotations

import time

from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from falabella_browser import ACTION_DELAY_SECONDS, LOGIN_URL
from falabella_pages.base import BasePage


class LoginPage(BasePage):
    def open(self) -> None:
        self.driver.get(LOGIN_URL)

    def is_authenticated(self) -> bool:
        return "/web-clientes/" in (self.driver.current_url or "")

    def open_account_menu(self) -> None:
        wait = self.wait
        account_button = wait.until(
            EC.element_to_be_clickable((By.XPATH, '//button[normalize-space()="Mi cuenta"]'))
        )
        account_button.click()
        time.sleep(ACTION_DELAY_SECONDS)

    def submit_login(self, username: str, password: str) -> None:
        wait = self.wait
        rut_input = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, 'input[placeholder="RUT"]')))
        password_input = wait.until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, 'input[placeholder="Clave Internet"]'))
        )
        rut_input.clear()
        rut_input.send_keys(username)
        time.sleep(ACTION_DELAY_SECONDS)
        password_input.clear()
        password_input.send_keys(password)
        time.sleep(ACTION_DELAY_SECONDS)

        submit = None
        candidates = self.driver.find_elements(By.CSS_SELECTOR, 'button[class*="login-button"]')
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

    def close_post_login_banner(self) -> None:
        wait = self.wait
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
            self.driver.execute_script("arguments[0].click();", button)
        time.sleep(ACTION_DELAY_SECONDS)

