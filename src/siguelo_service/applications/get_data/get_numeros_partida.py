from patchright.sync_api import Locator, Page

from .validators import asiento_tive_popup_response_validator


class GetNumerosPartida:
    @staticmethod
    def execute(page: Page) -> tuple[str, ...]:
        asiento_tive_button: Locator = page.locator(
            f"span:has-text('Acceder al asiento de inscripción y TIVE')"
        )
        if not asiento_tive_button.is_visible():
            return tuple()

        with page.expect_response(asiento_tive_popup_response_validator):
            asiento_tive_button.click()

        load_indicator_2: Locator = page.locator("#swal2-content")
        load_indicator_2.wait_for()
        load_indicator_2.wait_for(state="detached")
        page.wait_for_timeout(1000)

        # NOTE: i don't know if empty msg is inside a floating div.
        empty_p_element = page.locator(
            "p:has-text('Su búsqueda no ha obtenido resultados.')"
        )

        if empty_p_element.is_visible():
            page.keyboard.press("Escape")
            return tuple()

        td: Locator = page.locator("div.container tbody tr td:nth-child(2)")

        if not td.first.is_visible():
            return tuple()

        asiento_tive_partidas: tuple[str, ...] = tuple(
            map(str.strip, td.all_inner_texts())
        )

        close_button: Locator = page.locator("mat-icon", has_text="close")
        close_button.click()

        page.wait_for_timeout(500)

        return asiento_tive_partidas
