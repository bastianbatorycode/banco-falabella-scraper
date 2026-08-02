from __future__ import annotations

from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait


class BasePage:
    def __init__(self, driver: WebDriver):
        self.driver = driver

    @property
    def wait(self) -> WebDriverWait:
        return WebDriverWait(self.driver, 20)

