from datetime import datetime
from pathlib import Path

from patchright.sync_api import Page

from siguelo_service.models.dataclasses import CurrentSearch
from siguelo_service.scripts import INSERT_DIV_TO_SCREENSHOT_SCRIPT


class TakeScreenshot:
    @staticmethod
    def execute(
        page: Page,
        current_search: CurrentSearch,
        screenshot_dir: Path,
        type: str = "jpeg",
    ) -> Path:
        now = datetime.now()
        str_now = now.strftime("%d_%m_%Y__%H-%M-%S")
        cs_title = current_search.numero_titulo
        cs_title_year = current_search.anio_titulo
        ss_path = screenshot_dir / f"{cs_title}_{cs_title_year}__{str_now}.{type}"

        page.wait_for_load_state("load")
        page.mouse.click(0, 0)
        try:
            page.evaluate(INSERT_DIV_TO_SCREENSHOT_SCRIPT)
            page.wait_for_load_state("domcontentloaded")
            page.wait_for_timeout(1500)
            div_screenshot = page.locator("#div-screenshot")
            div_screenshot.screenshot(path=ss_path, type=type)  # type:ignore
        except Exception:
            page.screenshot(path=ss_path, type=type)  # type:ignore

        return ss_path
