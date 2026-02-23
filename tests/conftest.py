from typing import Generator

from patchright.sync_api import Browser, BrowserContext, sync_playwright
from pytest import fixture


@fixture(scope="session")
def browser_context_instance() -> Generator[BrowserContext, None, None]:
    with sync_playwright() as playwright:
        browser: Browser = playwright.chromium.launch(
            headless=False,
            channel="msedge",
            args=["--disable-popup-blocking", "--disable-notifications"],
        )
        browser_context: BrowserContext = browser.new_context()
        yield browser_context
        browser.close()
